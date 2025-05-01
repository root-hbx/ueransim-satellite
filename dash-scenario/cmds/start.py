import time
import logging
import os
from cmds.state import ROOT_DIR, FREE5GC_IP, save_state, load_state
from cmds.network import (
    start_gnb, start_ue, wait_for_uesimtun0_ip, 
    start_iperf_tcp_test, ensure_dir
)
from cmds.service_helper import start_wondershaper_service

def start_command(corenet, output_file=None, gen_time=30.0):
    """Start connection to a core network"""
    state = load_state()
    
    # Check if there's already a connection
    if state['gnb_pid'] or state['ue_pid']:
        logging.error("A connection is already active. Use 'switch' to change or 'stop' to terminate.")
        return False
    
    # Set default output file if none provided
    if not output_file:
        output_file = f"./test/{corenet}_tcp_traffic.txt"
    
    # Ensure output directory exists
    ensure_dir(output_file)
    
    # Record start time
    start_time = time.perf_counter()
    
    with open(output_file, "a") as f:
        f.write(f"[t=0] Connecting to {corenet}...\n")
        f.write(f"[t=0] Starting TCP traffic for {gen_time}s...\n")
    
    config_file = f"config/{corenet}-gnb.yaml"
    ue_config_file = f"config/{corenet}-ue.yaml"
    
    # Start gNB and UE
    gnb_pid = start_gnb(config_file)
    ue_pid = start_ue(ue_config_file)
    
    # Wait for interface to be ready
    try:
        interface_ip, built_time = wait_for_uesimtun0_ip(max_attempts=300, delay=0.1)
    except Exception as e:
        logging.error(f"Failed to get uesimtun0 IP: {e}")
        # Cleanup
        from cmds.network import terminate_processes
        terminate_processes(gnb_pid, ue_pid)
        return False
    
    # Start wondershaper
    start_wondershaper_service()
    
    service_start = time.perf_counter()
    
    # Start iperf TCP test
    iperf_pid = start_iperf_tcp_test(
        server_ip=FREE5GC_IP,
        interface_ip=interface_ip,
        port=5201,
        output_file=output_file,
        corenet_name=corenet,
        gen_time=gen_time,
        interval=1
    )
    
    # Save state
    state = {
        'gnb_pid': gnb_pid,
        'ue_pid': ue_pid,
        'interface_ip': interface_ip,
        'current_corenet': corenet,
        'start_time': start_time,
        'iperf_pid': iperf_pid
    }
    save_state(state)
    
    with open(output_file, "a") as f:
        f.write(f"[t = {built_time - start_time}] TCP Traffic Started from {interface_ip}...\n")
        f.write(f"[t = {service_start - start_time}] WonderShaper Service Started...\n")
    
    logging.info(f"Successfully connected to {corenet}")
    logging.info(f"Interface IP: {interface_ip}")
    
    return True