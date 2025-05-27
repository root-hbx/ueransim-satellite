import os
import subprocess
import time
import sys
import logging
import threading
import signal
from service_helper import (
    start_wondershaper_service, 
    stop_wondershaper_service, 
    restart_wondershaper_service
)
from network_sim import wait_for_uesimtun0_ip, ensure_dir
from fetch import fetch_file

"""
This script should be run on UERANSIM machine
"""

# Pls replace with your own path
ROOT_DIR = "/home/ueransim/ueransim-satellite"
# CDN_URL = "https://httpbin.org/drip?numbytes=104857600&duration=30&delay=1"
# FILE_NAME = "test.bin"
CDN_URL = "https://pub-cf250a7dff0b40dea71497e179a340b7.r2.dev/lecture12_SupML_buluc24.pdf"
FILE_NAME = "test.pdf"
STAGE_1_DURATION = 30 # seconds
BW_MAX = 200 # Mbps

logging.basicConfig(level=logging.INFO)

"""
Track curl process globally
- curl_process: ref for curl process
- curl_completed: sync for curl process completion
"""
curl_process = None
curl_completed = threading.Event()

def admin():
    """
    Check for sudo at first
    """
    print("=====================================================")
    print("== Authentication: Checking for sudo Permission ==")
    print("=====================================================")

    try:
        result = subprocess.run(
            ["sudo", "-v"], 
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("Passed! Now we are good :)")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Invalid Permissions: {e}")
        print("Failed! Plz check for your password as a root admin :(")
        sys.exit(1)


def terminate_processes(
    gnb_process: subprocess.Popen, 
    ue_process: subprocess.Popen
) -> None:
    """Terminate gNB and UE processes by Force && Clear uesimtun0 Network Interface"""
    if gnb_process:
        try:
            gnb_process.kill()
            logging.info("gNB process has been forcefully killed")
        except Exception as e:
            logging.error(f"Error killing gNB process: {e}")

    if ue_process:
        try:
            subprocess.run(["sudo", "pkill", "-f", "nr-ue"], check=True)
            logging.info("UE process has been forcefully killed")
        except Exception as e:
            logging.error(f"Error killing UE process: {e}")


def start_gnb(
    config_file: str) -> subprocess.Popen:
    """Start gNB with the given configuration file"""
    logging.info("Starting gNB...")
    gnb_cmd = [
        os.path.join(ROOT_DIR, "build/nr-gnb"),
        "-c",
        os.path.join(ROOT_DIR, config_file)
    ]
    gnb_process = subprocess.Popen(gnb_cmd, cwd=ROOT_DIR)
    logging.info(f"gNB process started (PID: {gnb_process.pid})")
    return gnb_process


def start_ue(
    config_file: str) -> subprocess.Popen:
    """Start UE with the given configuration file"""
    logging.info("Starting UE...")
    ue_cmd = [
        "sudo",
        os.path.join(ROOT_DIR, "build/nr-ue"),
        "-c",
        os.path.join(ROOT_DIR, config_file)
    ]
    ue_process = subprocess.Popen(ue_cmd, cwd=ROOT_DIR)
    logging.info(f"UE process started (PID: {ue_process.pid})")
    return ue_process


def send_sigint_to_curl() -> None:
    """Send SIGINT to the curl process, simulate Ctrl+C"""
    global curl_process
    if curl_process and curl_process.poll() is None:
        logging.info("Sending SIGINT to curl process...")
        try:
            # 使用 send_signal 而不是 killpg，这样更接近真实的Ctrl+C
            curl_process.send_signal(signal.SIGINT)
            logging.info("SIGINT sent to curl process successfully")
        except Exception as e:
            logging.error(f"Error sending SIGINT to curl: {e}")
            # 如果SIGINT失败，尝试terminate
            try:
                curl_process.terminate()
                logging.info("Curl process terminated")
            except Exception as kill_e:
                logging.error(f"Error terminating curl process: {kill_e}")
    else:
        logging.warning("Curl process not found or already terminated")


def cleanup_all_processes():
    global curl_process
    
    logging.info("Starting cleanup of all processes...")
    
    if curl_process and curl_process.poll() is None:
        try:
            curl_process.kill()
            curl_process.wait(timeout=3)
            logging.info("Curl process cleaned up")
        except Exception as e:
            logging.error(f"Error cleaning up curl process: {e}")
    
    try:
        subprocess.run(["pkill", "-f", "curl.*uesimtun0"], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "curl"], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL)
        logging.info("All curl processes killed")
    except:
        pass

    curl_process = None
    curl_completed.clear()


def run_scenario():
    """Run the main scenario for curl flow with two stages"""
    global curl_completed, curl_process
    output_file_stat = "./file-x/exp_stat.txt"
    output_file_logging = "./file-x/exp_logging.txt"
    ensure_dir(output_file_stat)
    ensure_dir(output_file_logging)

    gnb1_process = None
    ue1_process = None
    gnb2_process = None
    ue2_process = None

    # Record start time for logging as timestamp 0
    start_exp = time.perf_counter()
    with open(output_file_stat, "a") as f:
        f.write("[t=0] Connecting to open5gs-1...\n")
        f.write(f"CDN URL: {CDN_URL}\n")
        f.write(f"Duration for Stage 1: {STAGE_1_DURATION}\n")

    try:
        # [Phase 1] Start gNB and UE for open5gs-1
        gnb1_process = start_gnb("config/open5gs1-gnb.yaml")
        ue1_process = start_ue("config/open5gs1-ue.yaml")
        [interface1_ip, built1_probe] = wait_for_uesimtun0_ip(max_attempts=300, delay=0.1)
        
        start_wondershaper_service() # sync func, blocking
        tc_started_1 = time.perf_counter()

        # Phase 1: curl process without automatic interruption
        curl_completed.clear()
        curl_thread_1 = fetch_file(
            net_interface="uesimtun0",
            file_name=FILE_NAME,
            cdn_url=CDN_URL,
            log_file_path=output_file_logging,
            timeout=None,
            return_thread=True
        ) # async, non-blocking
        """
        - "curl process" -> curl_process <Popen Obj, PID=12345>
        - "curl_completed" -> false
        - "curl_thread_1" -> <Thread, name='fetch_file-uesimtun0-test.pdf'>
        """

        time.sleep(STAGE_1_DURATION)
        """
        1. main thread sleep for STAGE_1_DURATION seconds
        2. curl process is still running
        3. fetch_file thread is waiting for curl process to complete
        """
        
        # Step 1: Terminate open5gs1 connection
        logging.info("Step 1: Terminating open5gs1 connection...")
        start_to_close_1 = time.perf_counter()
        
        terminate_processes(gnb1_process, ue1_process)
        gnb1_process = None
        ue1_process = None
        logging.info("Step 1 completed: open5gs1 connection terminated")
        success_close_1 = time.perf_counter()
        """
        - "nr process" -> end
        - "curl process" -> still running
        - "curl_completed" -> false
        """
        
        # Step 2: After disconnection, send SIGINT to curl process
        logging.info("Step 2: Sending SIGINT to curl process...")
        send_sigint_to_curl() # async, non-blocking
        send_sigint = time.perf_counter()
        """
        send SIGINT to curl process, simulating Ctrl+C
        """
        
        # Step 3: Wait for curl process to terminate
        max_wait = 1000  # 1000 * 1ms = 1000ms
        wait_count = 0
        while curl_process and curl_process.poll() is None and wait_count < max_wait:
            time.sleep(0.001)  # 1ms
            wait_count += 1

        success_sigint = time.perf_counter()
        if wait_count >= max_wait:
            logging.warning("Curl process taking too long to terminate")
            cleanup_all_processes()
        else:
            logging.info(f"Curl process terminated after {wait_count}ms")

        with open(output_file_stat, "a") as f:
            f.write("\n[Phase 1]\n")
            f.write(f"Connecting with open5gs-1 need {(built1_probe - start_exp):.2f}s\n")
            f.write(f"Starting Wondershaper need {(tc_started_1 - built1_probe):.2f}s\n")
            f.write(f"[Actual] Stage-1 curl flow is lasting for {(start_to_close_1 - tc_started_1):.2f}s\n")
            f.write(f"[Theory] Stage-1 curl flow is lasting for {STAGE_1_DURATION:.2f}s\n")
            f.write(f"Disconnecting with open5gs1 need {(success_close_1 - start_to_close_1):.2f}s\n")
            f.write(f"Destructing curl process need {(success_sigint - send_sigint):.2f}s\n")

        # [Phase 2] Start gNB and UE for open5gs-2
        start_to_connect_2 = time.perf_counter()
        with open(output_file_stat, "a") as f:
            f.write(f"\n[t={start_to_connect_2 - start_exp}] Connecting to open5gs-2...\n")
            f.write(f"CDN URL: {CDN_URL}\n")
            f.write("Duration for Stage 2: TBD\n")
        
        gnb2_process = start_gnb("config/open5gs2-gnb.yaml")
        ue2_process = start_ue("config/open5gs2-ue.yaml")
        [interface2_ip, built2_probe] = wait_for_uesimtun0_ip(max_attempts=300, delay=0.1)
        
        restart_wondershaper_service()
        tc_started_2 = time.perf_counter()

        # Phase 2: curl process without interruption
        curl_completed.clear()
        curl_thread2 = fetch_file(
            net_interface="uesimtun0",
            file_name=FILE_NAME,
            cdn_url=CDN_URL,
            log_file_path=output_file_logging,
            timeout=None,
            return_thread=True
        )
        
        # Block main thread until curl process is terminated
        try:
            curl_thread2.join(timeout=120)  # 最多等待2分钟
            if curl_thread2.is_alive():
                logging.warning("Curl thread still alive after timeout, forcing cleanup")
                cleanup_all_processes()
        except Exception as e:
            logging.error(f"Error joining curl thread: {e}")
            cleanup_all_processes()
        
        curl_end_2 = time.perf_counter()

        with open(output_file_stat, "a") as f:
            f.write("\n[Phase 2]\n")
            f.write(f"Connecting with open5gs-2 need {(built2_probe - start_to_connect_2):.2f}s\n")
            f.write(f"Restarting Wondershaper need {(tc_started_2 - built2_probe):.2f}s\n")
            f.write(f"[Actual] Stage-2 curl flow is lasting for {(curl_end_2 - tc_started_2):.2f}s\n")
            f.write("[Theory] No reference\n")

    except Exception as e:
        logging.error(f"Exception in run_scenario: {e}")
        cleanup_all_processes()
        raise

    finally:
        stop_wondershaper_service()
        tc_end_2 = time.perf_counter()
        if gnb1_process or ue1_process:
            terminate_processes(gnb1_process, ue1_process)
        if gnb2_process or ue2_process:
            terminate_processes(gnb2_process, ue2_process)

        send_sigint_to_curl() # async, non-blocking
        all_done = time.perf_counter()

    logging.info(f"Results saved to {output_file_logging} and {output_file_stat}")
    logging.info("Scenario completed successfully")

    ###################################################
    # Write final statistics to the output file       #
    ###################################################
    total_prog_time = all_done - start_exp
    total_exp_time = total_prog_time - (tc_started_1 - built1_probe) - (tc_started_2 - built2_probe) - (tc_end_2 - curl_end_2)
    # Theoretically, switching_cost = ending_connection_with_open5gs1 + ending_curl_process + starting_connection_with_open5gs2
    switching_cost = built2_probe - start_to_close_1
    ending_connection_with_open5gs1 = success_close_1 - start_to_close_1
    ending_curl_process = success_sigint - send_sigint
    starting_connection_with_open5gs2 = built2_probe - start_to_connect_2

    with open(output_file_stat, "a") as f:
        f.write(f"Ending Wondershaper need {(tc_end_2 - curl_end_2):.2f}s\n")
        f.write(f"Disconnecting with open5gs2 need {(all_done - tc_end_2):.2f}s\n")
        f.write("\nStatistics:\n")
        f.write("---------------[Summary]------------------\n")
        f.write(f"Total Program Time: {total_prog_time:.2f}s\n")
        f.write(f"Total Experiment Time: {total_exp_time:.2f}s\n")
        f.write("----------[Impact of Switching]----------\n")
        f.write(f"Switching Cost: {switching_cost:.2f}s\n")
        f.write(f"Ending Connection with open5gs1: {ending_connection_with_open5gs1:.2f}s\n")
        f.write(f"Ending Curl Process: {ending_curl_process:.2f}s\n")
        f.write(f"Starting Connection with open5gs2: {starting_connection_with_open5gs2:.2f}s\n")


# Module Test
if __name__ == "__main__":
    admin()
    try:
        STAGE_1_DURATION = 30
        BW_MAX = 200 # Mbps
        run_scenario()
    except KeyboardInterrupt:
        logging.info("Program interrupted by user")
        cleanup_all_processes()
    except Exception as e:
        logging.error(f"Error for x (Stage 1 Duration) = {STAGE_1_DURATION}: {e}")
        cleanup_all_processes()
    finally:
        cleanup_all_processes()
        time.sleep(2)
        logging.info("Program exiting...")
        os._exit(0)

