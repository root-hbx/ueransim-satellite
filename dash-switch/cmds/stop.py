import time
import logging
import os
from cmds.state import load_state, clear_state 
from cmds.network import terminate_processes, rollback_default_route
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
    
    # Terminate processes
    terminate_processes(state['gnb_pid'], state['ue_pid'])
    
    # Rollback default route
    rollback_default_route()
    time.sleep(1)
    
    # Clear state
    clear_state()
    
    logging.info("Connection stopped successfully")
    return True


