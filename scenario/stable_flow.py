import os
import subprocess
import time
import sys
import logging
import threading
from network_sim import wait_for_uesimtun0_ip, iperf_tcp_test, ensure_dir

"""
This script should be run on UERANSIM machine
"""

# Pls replace with your own path
ROOT_DIR = "/home/ueransim/ueransim-satellite"
FREE5GC_IP = "172.16.162.135"
TOTAL_DATA = 500

logging.basicConfig(level=logging.INFO)

"""
Flow:
- 0-70s: Continuous TCP background traffic flow 
  * 0-70s: Through open5gs-1 (10.45.0.2)
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
    output_file = f"./std/continuous_tcp_traffic_{TOTAL_DATA}.txt"
    ensure_dir(output_file)

    gnb1_process = None
    ue1_process = None

    # Record start time for logging as timestamp 0
    # start_exp = time.time()
    with open(output_file, "a") as f:
        f.write("[t=0] Connecting to open5gs-1...")
        f.write(f"[t=0] Starting continuous TCP background traffic ({TOTAL_DATA}G One-Time ...")

    # Start gNB and UE for open5gs-1
    gnb1_process = start_gnb("config/open5gs1-gnb.yaml")
    ue1_process = start_ue("config/open5gs1-ue.yaml")
    [interface1_ip, built1_probe] = wait_for_uesimtun0_ip(max_attempts=15, delay=0.1)

    # Phase 1: Use interface1 for the first part
    phase_1_total_data = str(TOTAL_DATA - 0) + "G"
    iperf_tcp_test(
        server_ip=FREE5GC_IP,
        interface_ip=interface1_ip,
        port=5201,
        output_file=output_file,
        corenet_name="open5gs-1",
        totaldata=phase_1_total_data,
        interval=1,
    )

    tcp_end_time = time.time()
    tcp_total_time = tcp_end_time - built1_probe

    # Terminate first gNB and UE processes
    terminate_processes(gnb1_process, ue1_process)
    gnb1_process = None
    ue1_process = None

    with open(output_file, "a") as f:
        f.write("\nstatistics:\n")
        f.write(f"Total Data: {TOTAL_DATA}G\n")
        f.write(f"Total Time: {tcp_total_time:.4f} seconds\n")


if __name__ == "__main__":
    admin()

    # Default
    TOTAL_DATA = 10
    run_scenario()
    time.sleep(3)

    # Total Data
    for i in range(100, 210, 10):
        try:
            TOTAL_DATA = i
            run_scenario()
        except Exception as e:
            logging.error(f"Error for Total Data {TOTAL_DATA}: {e}")
        finally:
            time.sleep(3)

