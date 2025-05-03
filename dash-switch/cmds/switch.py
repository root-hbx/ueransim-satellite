import time
import logging
from cmds.state import save_state, load_state
from cmds.network import (
    terminate_processes, start_gnb, start_ue,
    add_default_route, del_default_route,
    wait_for_uesimtun0_ip, ensure_dir
)
from cmds.service_helper import stop_wondershaper_service, start_wondershaper_service


def switch_command(new_corenet="open5gs2", output_file=None):
    """Switch to a different core network"""
    ori_state = load_state()
    
    # Need an existing connection
    if not ori_state['gnb_pid'] and not ori_state['ue_pid']:
        logging.error("No active connection. Use 'start' first.")
        return False
    
    # Set default output file if none provided
    if not output_file:
        output_file = f"./test/switch_to_{new_corenet}_tcp_traffic.txt"
    
    # Ensure output directory exists
    ensure_dir(output_file)
    
    # Get old connection details
    old_corenet = ori_state['current_corenet']
    old_interface_ip = ori_state['interface_ip']
    original_start_time = ori_state['start_time']
    
    switch_start_time = time.perf_counter()
    
    with open(output_file, "a") as f:
        f.write(f"[t={switch_start_time - original_start_time}] Switching from {old_corenet} to {new_corenet}...\n")
    
    # Stop wondershaper service
    stop_wondershaper_service()
    
    # Terminate old processes
    terminate_processes(ori_state['gnb_pid'], ori_state['ue_pid'])
    
    termination_time = time.perf_counter()
    
    # Start new connection
    config_file = f"config/{new_corenet}-gnb.yaml"
    ue_config_file = f"config/{new_corenet}-ue.yaml"
    
    #TODO(bxhu): Remove uesimtun0 default route
    del_default_route("uesimtun0", None)
    
    # Start gNB and UE for new connection
    gnb_pid = start_gnb(config_file)
    ue_pid = start_ue(ue_config_file)
    
    # Wait for new interface to be ready
    try:
        interface_ip, built_time = wait_for_uesimtun0_ip(max_attempts=300, delay=0.1)
    except Exception as e:
        logging.error(f"Failed to get uesimtun0 IP: {e}")
        return False
    
    #TODO(bxhu): Add uesimtun0 IP to default route
    add_default_route("uesimtun0", None)
    
    # Start wondershaper
    start_wondershaper_service()

    service_start = time.perf_counter()
    
    # Update state
    updated_state = {
        'gnb_pid': gnb_pid,
        'ue_pid': ue_pid,
        'interface_ip': interface_ip,
        'current_corenet': new_corenet,
        'start_time': original_start_time,  # Keep original start time for total elapsed time
        'route_monitor_active': True,
    }
    save_state(updated_state)
    
    with open(output_file, "a") as f:
        f.write(f"[t = {termination_time - original_start_time}] Old connection terminated\n")
        f.write(f"[t = {built_time - original_start_time}] TCP Traffic Switching from {old_interface_ip} to {interface_ip}...\n")
        f.write(f"[t = {service_start - original_start_time}] WonderShaper Service Started...\n")
    
    logging.info(f"Successfully switched from {old_corenet} to {new_corenet}")
    logging.info(f"New Interface IP: {interface_ip}")
    
    return True


