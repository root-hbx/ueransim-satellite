import os
import subprocess
import time
import sys
import logging
import threading
from network_sim import wait_for_uesimtun0_ip ,iperf_tcp_test

"""
This script should be run on UERANSIM machine
"""

# Pls replace with your own path
ROOT_DIR = "/home/ueransim/ueransim-satellite"
FREE5GC_IP = "172.16.162.135"
BW4TCP = "1G"
TOTAL_DATA = 40
DIVIDE_DATA = 20

logging.basicConfig(level=logging.INFO)

"""
Flow:
- 0-70s: Continuous TCP background traffic flow 
  * 0-35s: Through open5gs-1 (10.45.0.2)
  * 35-70s: Through open5gs-2 (10.42.0.2)
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
    global BW4TCP
    output_file = f"./test/continuous_tcp_traffic_{BW4TCP}.txt"

    gnb1_process = None
    ue1_process = None
    gnb2_process = None
    ue2_process = None

    # Record start time for logging as timestamp 0
    start_exp = time.time()
    print("[t=0] Connecting to open5gs-1...")
    print("[t=0] Starting continuous TCP background traffic (40G Total, 20G Each)...")

    # Start gNB and UE for open5gs-1
    gnb1_process = start_gnb("config/open5gs1-gnb.yaml")
    ue1_process = start_ue("config/open5gs1-ue.yaml")
    [interface1_ip, built1_probe] = wait_for_uesimtun0_ip(max_attempts=15, delay=0.1)

    # Phase 1: Use interface1 for the first part
    phase_1_total_data = str(DIVIDE_DATA - 0) + "G"
    iperf_tcp_test(
        server_ip=FREE5GC_IP,
        interface_ip=interface1_ip,
        port=5201,
        output_file=output_file,
        corenet_name="open5gs-1",
        totaldata=phase_1_total_data,
        interval=1,
        bandwidth=BW4TCP,
    )

    # Terminate first gNB and UE processes
    terminate_processes(gnb1_process, ue1_process)
    gnb1_process = None
    ue1_process = None

    with open(output_file, "a") as f:
        f.write(f"[t = {built1_probe - start_exp}] TCP Traffic Switching TCP traffic from {interface1_ip}\n")
        f.write(f"[Phase 1] Data Transferred: {phase_1_total_data}\n")

    # Start gNB and UE for open5gs-2
    gnb2_process = start_gnb("config/open5gs2-gnb.yaml")
    ue2_process = start_ue("config/open5gs2-ue.yaml")
    [interface2_ip, built2_probe] = wait_for_uesimtun0_ip(max_attempts=15, delay=0.1)

    # Phase 2: Use interface2 for the second part
    phase_2_total_data = str(TOTAL_DATA - DIVIDE_DATA) + "G"
    iperf_tcp_test(
        server_ip=FREE5GC_IP,
        interface_ip=interface2_ip,
        port=5201,
        output_file=output_file,
        corenet_name="open5gs-2",
        totaldata=phase_2_total_data,
        interval=1,
        bandwidth=BW4TCP,
    )

    with open(output_file, "a") as f:
        f.write(f"[t = {built2_probe - start_exp}] TCP Traffic Switching TCP traffic from {interface1_ip} to {interface2_ip}\n")
        f.write(f"[Phase 2] Data Transferred: {phase_2_total_data}\n")

    # Terminate gNB and UE processes
    terminate_processes(gnb2_process, ue2_process)
    gnb2_process = None
    ue2_process = None

    logging.info(f"Results saved to {output_file}")
    logging.info("Scenario completed successfully")


if __name__ == "__main__":
    admin()

    # Default
    BW4TCP = "1G"
    run_scenario()
    time.sleep(3)
    
    # # Different bandwidth
    # for i in range(10, 310, 10):
    #     bw = f"{i}M"
    #     try:
    #         BW4TCP = bw
    #         run_scenario()
    #     except Exception as e:
    #         logging.error(f"Error during test with bandwidth {bw}: {e}")
    #     finally:
    #         time.sleep(3)