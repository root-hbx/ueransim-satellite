import os
import subprocess
import time
import sys
import logging
import threading
from network_sim import iperf_udp_test

"""
This script should be run on UERANSIM machine
"""

# Pls replace with your own path
ROOT_DIR = "/home/ueransim/ueransim-satellite"

FREE5GC_IP = "192.168.1.104"
OPEN5GS1_IP = "10.45.0.1"
OPEN5GS2_IP = "10.42.0.1"
UERSIMTUN1_IP = "10.45.0.2"
UERSIMTUN2_IP = "10.42.0.2"

logging.basicConfig(level=logging.INFO)

def admin():
    """
    Check for sudo at first
    """
    print("==========================================================")
    print("== Authentication: Checking for sudo Permission==")
    print("==========================================================")

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


def run_udp_background_traffic(
    server_ip: str,
    interface_ip: str,
    port: int = 5001,
    output_file: str = "./test/iperf_udp.txt",
    corenet_name: str = "",
    duration: int = 120,
    interval: int = 5,
):
    """Run UDP background traffic in a separate thread"""
    def run_traffic():
        iperf_udp_test(
            server_ip=server_ip,
            interface_ip=interface_ip,
            port=port,
            output_file=output_file,
            corenet_name=corenet_name,
            duration=duration,
            interval=5
        )

    thread = threading.Thread(target=run_traffic)
    thread.daemon = True  # Set as daemon

    logging.info("UDP background traffic started")
    thread.start()

    return thread


def run_scenario():
    """Constructing the scenario with time-controlled connections"""
    print("========================================")
    print("===         UDP Test Scenario        ===")
    print("========================================")

    gnb1_process = None
    ue1_process = None
    gnb2_process = None
    ue2_process = None
    udp1_thread = None
    udp2_thread = None

    # Record start time for logging as timestamp 0
    logging.info("[t=0] Connecting to open5gs-1...")
    logging.info("[t=0] Starting UDP background traffic (35s duration)...")
    
    # ==========================================================
    # Time to Start as t=0
    scenario_start = time.time()
    # ==========================================================
    
    # Start gNB and UE for open5gs-1
    gnb1_process = start_gnb("config/open5gs1-gnb.yaml")
    ue1_process = start_ue("config/open5gs1-ue.yaml")
    # Start UDP background traffic
    udp1_thread = run_udp_background_traffic(
        server_ip=FREE5GC_IP,
        interface_ip=UERSIMTUN1_IP,
        port=5001,
        output_file="./test/bgd_udp_stage1.txt",
        corenet_name="corenet-switching",
        duration=35,  # From t=0 to t=35
        interval=5
    )

    # ==========================================================
    # Wait until t=35 before disconnecting from open5gs-1
    elapsed = time.time() - scenario_start
    if elapsed < 35:
        time.sleep(35 - elapsed)
    # ==========================================================

    logging.info("[t=35] Disconnecting from open5gs-1...")
    # Terminate gNB and UE processes
    terminate_processes(gnb1_process, ue1_process)
    # Wait for the UDP thread to finish if it's still running
    if udp1_thread and udp1_thread.is_alive():
        udp1_thread.join(timeout=5)
    # Clear uesimtun0 open5gs-1 Network Interface
    gnb1_process = None
    ue1_process = None

    # ==========================================================
    # Wait until t=40 before connecting to open5gs-2
    elapsed = time.time() - scenario_start
    if elapsed < 40:
        time.sleep(40 - elapsed)
    # ==========================================================

    logging.info("[t=40] Connecting to open5gs-2...")
    logging.info("[t=40] Starting UDP background traffic (30s duration)...")
    # Start gNB and UE for open5gs-2
    gnb2_process = start_gnb("config/open5gs2-gnb.yaml")
    ue2_process = start_ue("config/open5gs2-ue.yaml")
    # Start UDP background traffic
    udp2_thread = run_udp_background_traffic(
        server_ip=FREE5GC_IP,
        interface_ip=UERSIMTUN2_IP,
        port=5001,
        output_file="./test/bgd_udp_stage2.txt",
        corenet_name="corenet-switching",
        duration=30,  # From t=40 to t=70
        interval=5
    )

    # ==========================================================
    # Wait until t=70 before disconnecting from open5gs-2
    elapsed = time.time() - scenario_start
    if elapsed < 70:
        time.sleep(70 - elapsed)
    # ==========================================================

    logging.info("[t=70] Disconnecting from open5gs-2...")
    # Terminate gNB and UE processes
    terminate_processes(gnb2_process, ue2_process)
    # Wait for the UDP thread to finish if it's still running
    if udp2_thread and udp2_thread.is_alive():
        udp2_thread.join(timeout=5)
    # Clear uesimtun1 open5gs-2 Network Interface
    gnb2_process = None
    ue2_process = None

    print("========================================")
    print("UDP Test Scenario Completed")
    print("========================================")
    logging.info("Theoretical Time: 65 seconds")
    logging.info(f"Actual Time: {time.time() - 5 - scenario_start:.4f} seconds")
    logging.info("Now you need to check the test result in ./test/test_bgd_udp.txt")
    logging.info("Scenario completed successfully")


if __name__ == "__main__":
    admin()
    run_scenario()
