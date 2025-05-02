import time
import logging
import os
from cmds.state import ROOT_DIR, save_state, load_state
from cmds.network import (
    start_gnb, start_ue, 
    wait_for_uesimtun0_ip, 
    ensure_dir
)
from cmds.service_helper import start_wondershaper_service


def start_command(corenet="open5gs1", output_file=None):
    """Start connection to a core network"""
    
    # Load current state
    state = load_state()
    
    # Check if there's already a connection
    if state['gnb_pid'] or state['ue_pid']:
        logging.error("A connection is already active. "
                    "Use 'switch' to change or 'stop' to terminate.")
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
    
    # Fetch Corresponding config files
    try: 
        config_file = os.path.join(ROOT_DIR, "config", f"{corenet}-gnb.yaml")
        ue_config_file = os.path.join(ROOT_DIR, "config", f"{corenet}-ue.yaml")
        if not os.path.exists(config_file) or not os.path.exists(ue_config_file):
            raise FileNotFoundError(f"Config files for {corenet} not found.")
    except FileNotFoundError as e:
        logging.error(e)
        return False
    except Exception as e:  
        logging.error(f"Unexpected error: {e}")
        return False
    
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
    
    # Save state
    state = {
        'gnb_pid': gnb_pid,
        'ue_pid': ue_pid,
        'interface_ip': interface_ip,
        'current_corenet': corenet,
        'start_time': start_time,
    }
    save_state(state)
    
    with open(output_file, "a") as f:
        f.write(f"[t = {built_time - start_time}] TCP Traffic Started from {interface_ip}...\n")
        f.write(f"[t = {service_start - start_time}] WonderShaper Service Started...\n")
    
    logging.info(f"Successfully connected to {corenet}")
    logging.info(f"Interface IP: {interface_ip}")
    
    return True


