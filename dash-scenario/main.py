import os
import subprocess
import time
import sys
import logging
import threading
from service_helper import start_wondershaper_service, stop_wondershaper_service
from network_sim import wait_for_uesimtun0_ip, iperf_tcp_test, ensure_dir

"""
This script should be run on UERANSIM machine
"""

# Pls replace with your own path
ROOT_DIR = "/home/ueransim/ueransim-satellite"
FREE5GC_IP = "172.16.162.135"
TOTAL_TIME = 60
DIVIDE_TIME = TOTAL_TIME / 2
BW_MAX = 200 # Mbps

logging.basicConfig(level=logging.INFO)

"""
Flow:
  * TCP Flow 1: 
    * Duration: TOTAL_TIME / 2
    * Link: open5gs-1
  * TCP Flow 2:
    * Duration: TOTAL_TIME / 2
    * Link: open5gs-2
Statistics:
  * Program Runtime: total_time
  * TCP Total Time: TOTAL_TIME
  * All Data Generated: total_data = total_time * BW_MAX / 8
  * All Data Transferred: pkt_size_1 + pkt_size_2
Experiments Plot:
  * x: TCP Total Time (`TOTAL_TIME`)
  * y1: All Data Transferred (`pkt_size_1 + pkt_size_2`)
  * y2: Link Rate Utilization (`All Data Transferred / All Data Generated`)
"""

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


def run_scenario():
    """Constructing the scenario with time-controlled connections"""
    output_file = f"./test/continuous_tcp_traffic_{TOTAL_TIME}.txt"
    ensure_dir(output_file)

    gnb1_process = None
    ue1_process = None
    gnb2_process = None
    ue2_process = None

    # Record start time for logging as timestamp 0
    start_exp = time.perf_counter()
    with open(output_file, "a") as f:
        f.write("[t=0] Connecting to open5gs-1...\n")
        f.write(f"[t=0] Starting continuous TCP background traffic {TOTAL_TIME}s Total, "
                f"{DIVIDE_TIME - 0}s for Stage-1, {TOTAL_TIME - DIVIDE_TIME}s for Stage-2...\n")

    # Start gNB and UE for open5gs-1
    gnb1_process = start_gnb("config/open5gs1-gnb.yaml")
    ue1_process = start_ue("config/open5gs1-ue.yaml")
    [interface1_ip, built1_probe] = wait_for_uesimtun0_ip(max_attempts=300, delay=0.1)
    # TODO(bxhu) sudo systemctl start wondershaper.service
    start_wondershaper_service() # must be called after uesimtun0 exists

    service_start_1 = time.perf_counter()

    # Phase 1: Use interface1 for the first part
    phase_1_duration = DIVIDE_TIME - 0
    iperf_tcp_test(
        server_ip=FREE5GC_IP,
        interface_ip=interface1_ip,
        port=5201,
        output_file=output_file,
        corenet_name="open5gs-1",
        gen_time=phase_1_duration,
        interval=1,
    )

    tcp_end_1 = time.perf_counter() # theoretically, tcp_end_1 = service_start_1 + phase_1_duration

    # TODO(bxhu) sudo systemctl stop wondershaper.service
    stop_wondershaper_service() # must be called before uesimtun0 is killed

    service_end_1 = time.perf_counter()

    # Terminate first gNB and UE processes
    terminate_processes(gnb1_process, ue1_process)
    gnb1_process = None
    ue1_process = None

    with open(output_file, "a") as f:
        f.write("\n[Phase 1]\n")
        f.write(f"[t = {built1_probe - start_exp}] TCP Traffic Started from {interface1_ip}...\n")
        f.write(f"[t = {service_start_1 - start_exp}] WonderShaper Service Started for Stage 1...\n")
        f.write(f"[Sender] TCP Traffic Generating for: {tcp_end_1 - service_start_1} s...\n")

    # Start gNB and UE for open5gs-2
    gnb2_process = start_gnb("config/open5gs2-gnb.yaml")
    ue2_process = start_ue("config/open5gs2-ue.yaml")
    [interface2_ip, built2_probe] = wait_for_uesimtun0_ip(max_attempts=300, delay=0.1)
    # TODO(bxhu) sudo systemctl start wondershaper.service
    start_wondershaper_service()

    service_start_2 = time.perf_counter()

    # Phase 2: Use interface2 for the second part
    phase_2_duration = TOTAL_TIME - DIVIDE_TIME
    iperf_tcp_test(
        server_ip=FREE5GC_IP,
        interface_ip=interface2_ip,
        port=5201,
        output_file=output_file,
        corenet_name="open5gs-2",
        gen_time=phase_2_duration,
        interval=1,
    )

    tcp_end_2 = time.perf_counter() # theoretically, tcp_end_2 = service_start_2 + phase_2_duration

    with open(output_file, "a") as f:
        f.write("\n[Phase 2]\n")
        f.write(f"[t = {built2_probe - start_exp}] TCP Traffic Switching from {interface1_ip} to {interface2_ip}...\n")
        f.write(f"[t = {service_start_2 - start_exp}] WonderShaper Service Started for Stage 2...\n")
        f.write(f"[Sender] TCP Traffic Generating for: {tcp_end_2 - service_start_2} s...\n")

    # Terminate gNB and UE processes
    # TODO(bxhu) sudo systemctl stop wondershaper.service
    stop_wondershaper_service()
    terminate_processes(gnb2_process, ue2_process)
    gnb2_process = None
    ue2_process = None

    logging.info(f"Results saved to {output_file}")
    logging.info("Scenario completed successfully")

    total_time = tcp_end_2 - service_start_1
    service_delay_1 = service_end_1 - tcp_end_1
    service_delay_2 = service_start_2 - built2_probe
    all_data_gen = total_time * BW_MAX / 8 # MB

    with open(output_file, "a") as f:
        f.write("\nStatistics:\n")
        f.write(f"All Data Generated: {(all_data_gen):.4f} MB\n") # need as part of "y2"
        f.write(f"Total TCP Time: {TOTAL_TIME:.4f} seconds\n") # need as "x"
        f.write(f"Total Run Time: {total_time:.4f} seconds\n")
        f.write(f"Service Delay 1: {service_delay_1:.4f} seconds\n")
        f.write(f"Service Delay 2: {service_delay_2:.4f} seconds\n")
        f.write(f"Switch Timeing Cost: {(total_time - TOTAL_TIME - service_delay_1 - service_delay_2):.4f} seconds\n")
        """
        Theoretically:
        Total Run Time = Total TCP Time + Service Delay 1 + Switch Timing Cost + Service Delay 2
        """


if __name__ == "__main__":
    admin()

    # Currently, BW_MAX = 200 Mbps by WonderShaper

    # # Default
    # TOTAL_TIME = 60
    # DIVIDE_TIME = TOTAL_TIME / 2
    # run_scenario()
    # time.sleep(10)

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

