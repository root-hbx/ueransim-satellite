import os
import time
import subprocess
import tempfile
import json
import logging


# Global constants
ROOT_DIR = "/home/ueransim/ueransim-satellite"
FREE5GC_IP = "172.16.162.135"
BW_MAX = 200  # Mbps

# State file for persisting running processes
STATE_FILE = os.path.join(tempfile.gettempdir(), "ueransim_state.json")

def save_state(state_data):
    """Save the current state to a file"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state_data, f)


def load_state():
    """Load the current state from file"""
    if not os.path.exists(STATE_FILE):
        return {
            'gnb_pid': None,
            'ue_pid': None,
            'interface_ip': None,
            'current_corenet': None,
            'start_time': None,
        }
    
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading state file: {e}")
        return {
            'gnb_pid': None,
            'ue_pid': None, 
            'interface_ip': None,
            'current_corenet': None,
            'start_time': None,
        }


def clear_state():
    """Clear the current state"""
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)


