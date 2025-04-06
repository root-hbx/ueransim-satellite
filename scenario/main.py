import os
import subprocess
import time
import logging

ROOT_DIR = "/Users/huluobo/Github_Content/ueransim-satellite"

def terminate_processes(
    gnb_process: subprocess.Popen | None, 
    ue_process: subprocess.Popen | None
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
    print("Scenario Creating...")

    print("======================================================")
    print("== Phase 1: Traffic through CoreNet 1 (10.45.0.0/16) ==")
    print("======================================================")
    
    gnb1_process = None
    ue1_process = None
    
    gnb1_process = start_gnb("config/open5gs1-gnb.yaml")
    time.sleep(3) # Wait for gNB to complete
    ue1_process = start_ue("config/open5gs1-ue.yaml")

    #TODO(bxhu): add `ping -I uersimtun0 192.168.0.1` via open5gs1

    print("Waiting for 2 minutes, currently interacting with open5gs1...")
    time.sleep(120)

    terminate_processes(gnb1_process, ue1_process)

    print("======================================================")
    print("Waiting for 5 seconds before starting the next phase")
    print("======================================================")
    time.sleep(5)

    print("======================================================")
    print("== Phase 2: Traffic through CoreNet 2 (10.42.0.0/16) ==")
    print("======================================================")

    gnb2_process = None
    ue2_process = None

    gnb2_process = start_gnb("config/open5gs2-gnb.yaml")
    time.sleep(3) # Wait for gNB to complete
    ue2_process = start_ue("config/open5gs2-ue.yaml")
    
    #TODO(bxhu): add `ping -I uersimtun0 192.168.0.1` via open5gs2

    print("Waiting for 2 minutes, currently interacting with open5gs2...")
    time.sleep(120)

    terminate_processes(gnb2_process, ue2_process)


if __name__ == "__main__":
    run_scenario()
