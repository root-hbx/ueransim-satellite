import time
import logging
import os
from cmds.state import load_state, clear_state 
from cmds.network import (
    terminate_processes,
    add_default_route,
    del_default_route,
    stop_route_monitor,
)
from cmds.service_helper import stop_wondershaper_service


def stop_command():
    """Stop current connection"""
    state = load_state()
    
    # Check if there's an active connection
    if not state['gnb_pid'] and not state['ue_pid']:
        logging.warning("No active connection to stop.")
        return True
    
    # Stop wondershaper service
    stop_wondershaper_service()
    
    #TODO(bxhu): Remove uesimtun0 default route
    del_default_route()
    
    # Terminate processes
    terminate_processes(state['gnb_pid'], state['ue_pid'])
    time.sleep(1)
    
    if state.get('route_monitor_active', False):
        stop_route_monitor(state.get('stop_event'))

    # Clear state
    clear_state()
    
    #TODO(bxhu): Add ens33 default route
    add_default_route("ens33", "172.16.162.2")

    logging.info("Connection stopped successfully")
    return True


