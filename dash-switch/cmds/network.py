import os
import subprocess
import time
import logging
from cmds.state import ROOT_DIR


def ensure_dir(file_path):
    """Ensure directory exists for the given file path"""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)


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


# def modify_default_route():
#     """
#     Modify the default route to use uesimtun0 instead of ens33.
#     1. Delete default route for ens33
#     2. Add uesimtun0 as the default route
#     3. Showcase current situation
#     """
    
#     print("==========================================")
#     print("Modifying the default route to ueransim...")
#     print("==========================================")
    
#     # 0. Release DHCP lease to prevent auto-renewal
#     # Do not use "dhclient -r" as it may cause issues with DNS
#     # try:
#     #     subprocess.run(["sudo", "systemctl", "stop", "NetworkManager"], check=False)
#     #     logging.info("Stopped NetworkManager to prevent route updates")
#     # except Exception as e:
#     #     logging.error(f"Error releasing DHCP lease: {str(e)}")
    
#     # 1. Del ens33
#     try:
#         subprocess.run(["sudo", "ip", "route", "del", "default"], check=False)
#         logging.info("All default routes deleted")
#     except Exception as e:
#         logging.error(f"Error deleting routes: {str(e)}")
    
#     # 2. Add uesimtun0
#     try:
#         subprocess.run(["sudo", "ip", "route", "add", "default", "dev", "uesimtun0"], check=True)
#         logging.info("uesimtun0 default route added")
#     except subprocess.CalledProcessError as e:
#         logging.info(f"{str(e)}")
#         return False
    
#     # 3. show current situation
#     print()
#     show_default_route()
    
#     return True


# def rollback_default_route():
#     """Rollback the default route to ens33"""
    
#     print("==========================================")
#     print("Rolling back the default route to ens33...")
#     print("==========================================")
    
#     # 1. Delete all default routes (including uesimtun0)
#     try:
#         subprocess.run(["sudo", "ip", "route", "del", "default"], check=False)
#         logging.info("All default routes deleted")
#     except Exception as e:
#         logging.error(f"Error deleting routes: {str(e)}")
    
#     # 2. Restart DHCP client to get proper configuration
#     # try:
#     #     subprocess.run(["sudo", "systemctl", "start", "NetworkManager"], check=False)
#     #     logging.info("NetworkManager restarted")
#     #     time.sleep(3)
#     # except Exception as e:
#     #     logging.error(f"Error restarting DHCP client: {str(e)}")
    
#     # 3. show current situation
#     print()
#     show_default_route()
    
#     return True

def add_default_route(interface: str, gateway: str):
    """
    Add a default route for the specified interface
    
    Args:
        interface: Network interface name (e.g., 'ens33', 'uesimtun0')
        gateway: Gateway/next hop IP address (optional)
    """
    try:
        if gateway:
            # Add default route with gateway address
            # "sudo ip route add default via 172.16.162.2 dev ens33"
            subprocess.run(["sudo", "ip", "route", "add", "default", "via", gateway, "dev", interface], check=True)
            logging.info(f"Default route added for {interface} via gateway {gateway} (for default date route)")
        else:
            # Add default route without gateway (direct link)
            # "sudo ip route add default dev ens33"
            subprocess.run(["sudo", "ip", "route", "add", "default", "dev", interface], check=True)
            logging.info(f"Default route added for {interface} (direct link, for open5gs)")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error adding default route: {str(e)}")
        return False
    
    show_default_route()
    return True
    

def del_default_route():
    """Delete the default route"""
    try:
        subprocess.run(["sudo", "ip", "route", "del", "default"], check=True)
        logging.info("Default route deleted")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error deleting default route: {str(e)}")
        return False
    
    show_default_route()
    return True


def show_default_route():
    """Show the current default route"""
    print("-------------------------------------")
    print("Showing the default route...")
    print("-------------------------------------")
    
    try:
        # result = subprocess.run(["ip", "route", "show", "default"], 
        #                       capture_output=True, text=True, check=True)
        result = subprocess.run(["ip", "route", "show"], 
                            capture_output=True, text=True, check=True)
        print("Current Default Route:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error: {str(e)}")
    
    return True

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


