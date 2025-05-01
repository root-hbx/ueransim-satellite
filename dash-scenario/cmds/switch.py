import time
import logging
import os
from cmds.state import ROOT_DIR, FREE5GC_IP, save_state, load_state
from cmds.network import (
    terminate_processes, start_gnb, start_ue, 
    wait_for_uesimtun0_ip, start_iperf_tcp_test, ensure_dir
)
from cmds.service_helper import stop_wondershaper_service, start_wondershaper_service

def switch_command(new_corenet, output_file=None, gen_time=30.0):
    """Switch to a different core network"""
    state = load_state()
    
    # Check if there's an active connection
    if not state['gnb_pid'] and not state['ue_pid']:
        logging.error("No active connection. Use 'start' first.")
        return False
    
    # Set default output file if none provided
    if not output_file:
        output_file = f"./test/switch_to_{new_corenet}_tcp_traffic.txt"
    
    # Ensure output directory exists
    ensure_dir(output_file)
    
    # Get old connection details
    old_corenet = state['current_corenet']
    old_interface_ip = state['interface_ip']
    original_start_time = state['start_time']
    
    switch_start_time = time.perf_counter()
    
    with open(output_file, "a") as f:
        f.write(f"[t={switch_start_time - original_start_time}] Switching from {old_corenet} to {new_corenet}...\n")
    
    # Stop wondershaper service
    stop_wondershaper_service()
    
    # Terminate old processes
    terminate_processes(state['gnb_pid'], state['ue_pid'])
    
    termination_time = time.perf_counter()
    
    # Start new connection
    config_file = f"config/{new_corenet}-gnb.yaml"
    ue_config_file = f"config/{new_corenet}-ue.yaml"
    
    # Start gNB and UE for new connection
    gnb_pid = start_gnb(config_file)
    ue_pid = start_ue(ue_config_file)
    
    # Wait for new interface to be ready
    try:
        interface_ip, built_time = wait_for_uesimtun0_ip(max_attempts=300, delay=0.1)
    except Exception as e:
        logging.error(f"Failed to get uesimtun0 IP: {e}")
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
        corenet_name=new_corenet,
        gen_time=gen_time,
        interval=1
    )
    
    # Update state
    state = {
        'gnb_pid': gnb_pid,
        'ue_pid': ue_pid,
        'interface_ip': interface_ip,
        'current_corenet': new_corenet,
        'start_time': original_start_time,  # Keep original start time for total elapsed time
        'iperf_pid': iperf_pid
    }
    save_state(state)
    
    with open(output_file, "a") as f:
        f.write(f"[t = {termination_time - original_start_time}] Old connection terminated\n")
        f.write(f"[t = {built_time - original_start_time}] TCP Traffic Switching from {old_interface_ip} to {interface_ip}...\n")
        f.write(f"[t = {service_start - original_start_time}] WonderShaper Service Started...\n")
    
    logging.info(f"Successfully switched from {old_corenet} to {new_corenet}")
    logging.info(f"New Interface IP: {interface_ip}")
    
    return True