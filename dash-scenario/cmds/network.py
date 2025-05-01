import os
import subprocess
import time
import socket
import logging
import threading
from cmds.state import ROOT_DIR, FREE5GC_IP
from cmds.service_helper import start_wondershaper_service, stop_wondershaper_service

def start_gnb(config_file):
    """Start gNB with the given configuration file"""
    logging.info("Starting gNB...")
    gnb_cmd = [
        os.path.join(ROOT_DIR, "build/nr-gnb"),
        "-c",
        os.path.join(ROOT_DIR, config_file)
    ]
    gnb_process = subprocess.Popen(gnb_cmd, cwd=ROOT_DIR)
    logging.info(f"gNB process started (PID: {gnb_process.pid})")
    return gnb_process.pid

def start_ue(config_file):
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
    return ue_process.pid

def wait_for_uesimtun0_ip(max_attempts=300, delay=0.1):
    """Wait for uesimtun0 to get an IP address"""
    logging.info("Waiting for uesimtun0 interface to be available...")
    attempts = 0
    
    while attempts < max_attempts:
        try:
            # Get IP address of uesimtun0
            ip_cmd = ["ip", "addr", "show", "uesimtun0"]
            ip_output = subprocess.check_output(ip_cmd).decode()
            
            # Extract IP address
            for line in ip_output.split("\n"):
                if "inet" in line and "inet6" not in line:
                    ip_address = line.strip().split()[1].split("/")[0]
                    logging.info(f"uesimtun0 IP address: {ip_address}")
                    return [ip_address, time.perf_counter()]
        except (subprocess.CalledProcessError, IndexError):
            pass
        
        attempts += 1
        time.sleep(delay)
    
    raise Exception("Failed to get IP address for uesimtun0")

def terminate_processes(gnb_pid, ue_pid):
    """Terminate gNB and UE processes"""
    if gnb_pid:
        try:
            subprocess.run(["kill", "-9", str(gnb_pid)], check=False)
            logging.info(f"gNB process (PID: {gnb_pid}) has been killed")
        except Exception as e:
            logging.error(f"Error killing gNB process: {e}")

    if ue_pid:
        try:
            subprocess.run(["sudo", "pkill", "-f", "nr-ue"], check=False)
            logging.info("UE process has been killed")
        except Exception as e:
            logging.error(f"Error killing UE process: {e}")

def start_iperf_tcp_test(server_ip, interface_ip, port, output_file, corenet_name, gen_time, interval=1):
    """Start iperf TCP test in the background and return the process"""
    iperf_cmd = [
        "iperf3",
        "-c", server_ip,
        "-B", interface_ip,
        "-p", str(port),
        "-t", str(gen_time),
        "-i", str(interval),
        "-b", f"{BW_MAX}M"
    ]
    
    logging.info(f"Starting iperf3 TCP test to {server_ip} via {interface_ip}...")
    
    if output_file:
        with open(output_file, "a") as f:
            f.write(f"[iperf3] Starting TCP test to {server_ip} via {interface_ip} for {gen_time}s\n")
    
    iperf_process = subprocess.Popen(iperf_cmd)
    logging.info(f"iperf3 process started (PID: {iperf_process.pid})")
    
    return iperf_process.pid

def ensure_dir(file_path):
    """Ensure directory exists for the given file path"""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)