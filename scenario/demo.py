import os
import subprocess
import time
import sys
import logging
from network_sim import ping_test, iperf_tcp_test, iperf_udp_test

"""
Demo for Meeting: Take Open5GS-2 as an example
"""

# Pls replace with your own path
ROOT_DIR = "/home/ueransim/ueransim-satellite"

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
    logging.info("(1) Starting gNB...")
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
    logging.info("(2) Starting UE...")
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

    print("==========================================================")
    print("== Waiting for 5 seconds before starting the next phase ==")
    print("==========================================================")
    time.sleep(5)

    print("=======================================================")
    print("== Phase 2: Traffic through CoreNet 2 (10.42.0.0/16) ==")
    print("=======================================================")

    gnb2_process = None
    ue2_process = None

    gnb2_process = start_gnb("config/open5gs2-gnb.yaml")
    time.sleep(3) # Wait for gNB to complete
    ue2_process = start_ue("config/open5gs2-ue.yaml")
    time.sleep(3) # Wait for UE to complete

    # ping -I uesimtun0 172.16.162.135 via open5gs2
    ping_test(
        target_ip="172.16.162.135",
        interface="uesimtun0",
        count=10,
        output_file="./test/ping_open5gs2.txt",
        corenet_name="open5gs2"
    )

    # TODO(bxhu): Start to Observe Traffic Performance (TCP/UDP Probe)
    """
    - Server: iperf -s -B 10.42.0.1
    - Client: iperf -u -c 10.42.0.1 -t 120 -i 5 --bind 10.42.0.2 > ./test/iperf_tcp.txt 2>&1
    """
    iperf_tcp_test(
        server_ip="10.42.0.1",
        interface_ip="10.42.0.2",
        output_file="./test/iperf_tcp_open5gs2.txt",
        corenet_name="open5gs2",
        duration=120,
        interval=5
    )
    """
    - Server: iperf -s -B 10.42.0.1
    - Client: iperf -u -c 10.42.0.1 -t 120 -i 5 --bind 10.42.0.2 > ./test/iperf_udp.txt 2>&1
    """
    iperf_udp_test(
        server_ip="10.42.0.1",
        interface_ip="10.42.0.2",
        output_file="./test/iperf_udp_open5gs2.txt",
        corenet_name="open5gs2",
        duration=120,
        interval=5
    )

    terminate_processes(gnb2_process, ue2_process)


if __name__ == "__main__":
    admin()
    run_scenario()
