import os
import json
import logging


# Global constants
ROOT_DIR = "/home/ueransim/ueransim-satellite"
FREE5GC_IP = "172.16.162.135"
BW_MAX = 200  # Mbps

# State file for persisting running processes
STATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "state")
if not os.path.exists(STATE_DIR):
    os.makedirs(STATE_DIR)

# dash-switch/state/ueransim_state.json
STATE_FILE = os.path.join(STATE_DIR, "ueransim_state.json")

def save_state(state_data):
    """Save the current state to a file"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state_data, f)
    show_ps_state()


def load_state():
    """Load the current state from file"""
    if not os.path.exists(STATE_FILE):
        return {
            'gnb_pid': None,
            'ue_pid': None,
            'interface_ip': None,
            'current_corenet': None,
            'start_time': None,
            'route_monitor_active': False,
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
            'route_monitor_active': False,
        }
    show_ps_state()


def clear_state():
    """Clear the current state"""
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    show_ps_state()


def show_ps_state():
    """Show the current state of the system"""
    state = load_state()
    print("Current State:")
    print(f"- gNB PID: {state['gnb_pid']}")
    print(f"- UE PID: {state['ue_pid']}")
    print(f"- Interface IP: {state['interface_ip']}")
    print(f"- Current Core Network: {state['current_corenet']}")
    print(f"- Start Time: {state['start_time']}")
    print(f"- Route Monitor Active: {state['route_monitor_active']}")
    
    
