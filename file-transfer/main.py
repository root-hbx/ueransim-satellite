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
CDN_URL = "https://pub-cf250a7dff0b40dea71497e179a340b7.r2.dev"
FILE_NAME = "test.pdf"
STAGE_1_DURATION = 5 # seconds
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
            os.killpg(os.getpgid(curl_process.pid), signal.SIGINT)
            logging.info("SIGINT sent to curl process successfully")
        except Exception as e:
            logging.error(f"Error sending SIGINT to curl: {e}")
    else:
        logging.warning("Curl process not found or already terminated")


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
            interrupt_after=None
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
        logging.info("Step 2 completed: SIGINT sent to curl")
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
        else:
            logging.info(f"Curl process terminated after {wait_count}ms")

        with open(output_file_logging, "a") as f:
            f.write("\n[Phase 1]\n")

        # [Phase 2] Start gNB and UE for open5gs-2
        start_to_connect_2 = time.perf_counter()
        
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
            interrupt_after=None
        )
        
        # Block main thread until curl process is terminated
        curl_thread2.join()

        with open(output_file_stat, "a") as f:
            f.write("\n[Phase 2]\n")

    finally:
        stop_wondershaper_service()
        if gnb1_process or ue1_process:
            terminate_processes(gnb1_process, ue1_process)
        if gnb2_process or ue2_process:
            terminate_processes(gnb2_process, ue2_process)
        all_done = time.perf_counter()

    logging.info(f"Results saved to {output_file_logging} and {output_file_stat}")
    logging.info("Scenario completed successfully")

    with open(output_file_stat, "a") as f:
        f.write("\nStatistics:\n")


if __name__ == "__main__":
    admin()

    # Total Data
    for i in range(10, 210, 10):
        try:
            TOTAL_TIME = i
            DIVIDE_TIME = TOTAL_TIME / 2
            run_scenario()
        except Exception as e:
            logging.error(f"Error for x (Pure TCP Time) = {TOTAL_TIME}: {e}")
        finally:
            time.sleep(10)


