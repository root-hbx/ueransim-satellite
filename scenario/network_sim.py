import subprocess
import logging
import sys
import os

"""
Network Helpers for Main
Should be used in main.py, running on UERANSIM machine
"""

logging.basicConfig(level=logging.INFO)

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)


def iperf_udp_test(
    server_ip: str,
    interface_ip: str,
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

    print("========================================================")
    print(f"=== iPerf UDP Test {server_ip} via {corenet_name} ===")
    print("========================================================")

    try:
        # Use subprocess.run to execute the command and redirect output
        with open(output_file, 'a') as out_file: # attach rather than overwrite
            process = subprocess.run(
                iperf_cmd,
                stdout=out_file,
                stderr=subprocess.STDOUT,
                check=True
            )
        print("====== iPerf Completed Successfully ======")
        logging.info(f"iPerf Test Successful - {corenet_name}")
        return True
    except subprocess.CalledProcessError as e:
        print("====== iPerf Failed ======")
        logging.error(f"iPerf Test Failed - {corenet_name}: {str(e)}")
        return False
    except Exception as e:
        print(f"====== iPerf Error: {str(e)} ======")
        logging.error(f"iPerf Test Error: {str(e)}")
        return False
