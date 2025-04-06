import os
import subprocess
import time
import logging
from network_sim import ping_test, iperf_tcp_test, iperf_udp_test

# Pls replace with your own path
ROOT_DIR = "/home/ueransim/ueransim-satellite"

def terminate_processes(
    gnb_process: subprocess.Popen, 
    ue_process: subprocess.Popen
) -> None:
    '''Terminate gNB and UE processes'''
    if gnb_process:
        gnb_process.terminate()
        gnb_process.wait(timeout=5)
        print("gNB process has been terminated")

    if ue_process:
        os.system(f"sudo kill {ue_process.pid}")
        print("UE process has been terminated")


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
    """Constructing the scenario with gNB and UE"""
    print("Scenario Creating...")
    print("=======================================================")
    print("== Phase 1: Traffic through CoreNet 1 (10.45.0.0/16) ==")
    print("=======================================================")

    gnb1_process = None
    ue1_process = None

    gnb1_process = start_gnb("config/open5gs1-gnb.yaml")
    time.sleep(3) # Wait for gNB to complete
    ue1_process = start_ue("config/open5gs1-ue.yaml")
    time.sleep(3) # Wait for UE to complete

    # ping -I uesimtun0 172.16.162.135 via open5gs1
    ping_test(
        target_ip="172.16.162.135",
        interface="uesimtun0",
        count=10,
        output_file="./test/ping_open5gs1.txt",
        corenet_name="open5gs1"
    )

    # TODO(bxhu): Start to Observe Traffic Performance (TCP/UDP Probe)
    """
    - Server: iperf -s -B 10.45.0.1
    - Client: iperf -u -c 10.45.0.1 -t 120 -i 5 --bind 10.45.0.2 > ./test/iperf_tcp.txt 2>&1
    """
    iperf_tcp_test(
        server_ip="10.45.0.1",
        interface="10.45.0.2",
        output_file="./test/iperf_tcp_open5gs1.txt",
        corenet_name="open5gs1",
        duration=120,
        interval=5
    )
    """
    - Server: iperf -s -B 10.45.0.1
    - Client: iperf -u -c 10.45.0.1 -t 120 -i 5 --bind 10.45.0.2 > ./test/iperf_udp.txt 2>&1
    """
    iperf_udp_test(
        server_ip="10.45.0.1",
        interface="10.45.0.2",
        output_file="./test/iperf_udp_open5gs1.txt",
        corenet_name="open5gs1",
        duration=120,
        interval=5
    )

    print("Waiting for 2 minutes, currently interacting with open5gs1...")
    time.sleep(160)

    terminate_processes(gnb1_process, ue1_process)

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
        interface="10.42.0.2",
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
        interface="10.42.0.2",
        output_file="./test/iperf_udp_open5gs2.txt",
        corenet_name="open5gs2",
        duration=120,
        interval=5
    )

    print("Waiting for 2 minutes, currently interacting with open5gs2...")
    time.sleep(160)

    terminate_processes(gnb2_process, ue2_process)


if __name__ == "__main__":
    run_scenario()
