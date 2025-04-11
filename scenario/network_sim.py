import subprocess
import logging
import sys
import os
import re
import functools

"""
Network Helpers for Main
Should be used in main.py, running on UERANSIM machine
"""

logging.basicConfig(level=logging.INFO)

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)


def wait_for_uesimtun0_ip(max_attempts=10, delay=1):
    """Wait until uesimtun0 interface is ready and has an IP address"""
    logging.info("Waiting for uesimtun0 interface to be ready...")
    
    for attempt in range(max_attempts):
        try:
            ip = get_uesimtun0_ip()
            if ip:
                logging.info(f"uesimtun0 interface is ready with IP: {ip}")
                return ip
        except Exception as e:
            logging.debug(f"Attempt {attempt+1}/{max_attempts}: uesimtun0 not ready yet ({str(e)})")
        
        time.sleep(delay)

    raise ValueError(f"Failed to get uesimtun0 IP after {max_attempts} attempts")


def get_uesimtun0_ip():
    """Get IP of uesimtun0 Network Interface"""
    try:
        result = subprocess.run(
            ["ifconfig", "uesimtun0"],
            capture_output=True,
            text=True,
            check=True
        )

        # Use regex to extract the IP address from the output
        ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout)
        if ip_match:
            return ip_match.group(1)
        return None
    except subprocess.CalledProcessError:
        logging.error("Cannot get uesimtun0 IP address: ifconfig failed")
        return None
    except Exception as e:
        logging.error(f"Error when fetching uesimtun0's IP: {str(e)}")
        return None


# def auto_fetch_uesimtun0_ip(func):
#     # func: iperf_udp_test
#     @functools.wraps(func) # functools: preserve metadata of the original function
#     def wrapper(*args, **kwargs):
#         # args: arbitrary positional arguments
#         # kwargs: arbitrary keyword arguments
#         assert 'interface_ip' not in kwargs or kwargs['interface_ip'] is None, \
#             "interface_ip cannot be specified because auto-fetch"

#         ip = get_uesimtun0_ip()
#         if ip:
#             logging.info(f"Auto-fetch uesimtun0 IP: {ip}")
#             kwargs['interface_ip'] = ip
#         else:
#             raise ValueError("Cannot auto-fetch uesimtun0 IP, plz specify interface_ip")
#         return func(*args, **kwargs)

#     return wrapper


# @auto_fetch_uesimtun0_ip
def iperf_udp_test(
    server_ip: str,
    interface_ip: str = None,
    port: int = 5001,
    output_file: str = "./test/iperf_udp.txt",
    corenet_name: str = "",
    duration: float = 120,
    interval: float = 5,
    bandwidth: str = "1M", # "1K" | "1M" | "1G"
) -> bool:
    """
    Server: iperf -u -s -p 5001
    Client: iperf -u -c [SERVER_IP] -p 5001 -t 120 -i 5 --bind [UESIMTUN0_IP] > ./test/iperf_udp.txt 2>&1

    Args:
        server_ip: Server IP address (free5gc VM, for test)
        interface_ip: net interface ip, default uesimtun0 (10.45.0.2 / 10.42.0.2)
        output_file: output file path
        corenet_name: corenet name, for logging

    Returns:
        bool: True if iperf is successful, False otherwise
    """

    logging.info(f"iperf Test (UDP): Connecting to {server_ip} "
                f"via {corenet_name if corenet_name else interface_ip}...")
    logging.info(f"iperf Test (UDP): Bandwidth {bandwidth}")
    logging.info(f"iperf Test (UDP): Network Interface is {interface_ip}")

    ensure_dir(output_file)
    iperf_cmd = [
        "sudo",
        "iperf",
        "-u", 
        "-c", server_ip,
        "-p", str(port),
        "-t", str(duration),
        "-i", str(interval),
        "-b", bandwidth,
        "--bind", interface_ip,
    ]

    print("=========================================================================")
    print(f"=== iPerf UDP Test: {interface_ip} -> {server_ip} via {corenet_name} ===")
    print("=========================================================================")

    try:
        # Use subprocess.run to execute the command and redirect output
        with open(output_file, 'a') as out_file: # attach rather than overwrite
            process = subprocess.run(
                iperf_cmd,
                stdout=out_file,
                stderr=subprocess.STDOUT,
                check=True
            )
            out_file.write(f"Current NetInterface IP: {interface_ip}\n")
            out_file.write(f"iPerf Test Successful - {corenet_name}\n")
        logging.info(f"iPerf Test Successful - {corenet_name}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"iPerf Test Failed - {corenet_name}: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"iPerf Test Error: {str(e)}")
        return False


# if __name__ == "__main__":
#     # For Test
#     iperf_udp_test(
#         server_ip="198.19.249.234",
#         interface_ip=None,  # auto-fetch uesimtun0 IP
#         port=5001,
#         output_file="./test/iperf_udp.txt",
#         corenet_name="test-auto-fetch",
#         duration=30,
#         interval=5,
#         bandwidth="1M",
#     )
