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


def ping_test(
    target_ip: str,
    interface: str = "uesimtun0",
    count: int = 15,
    output_file: str = "./test/ping.txt",
    corenet_name: str = ""
) -> bool:
    """
    ping -I uesimtun0 172.16.162.135 > ./test/ping.txt 2>&1

    Args:
        target_ip: target IP address (free5gc VM, for test)
        interface: net interface, default uesimtun0
        count: ping pkt num
        output_file: output file path
        corenet_name: corenet name, for logging

    Returns:
        bool: True if ping is successful, False otherwise
    """

    logging.info(f"Ping Test: Transmitting {count} packets to {target_ip} "
                f"via {corenet_name if corenet_name else interface}...")
    ensure_dir(output_file)
    ping_cmd = ["sudo", "ping", "-I", interface, "-c", str(count), target_ip]

    print("========================================================")
    print(f"=== PING Test {target_ip} via {corenet_name} ===")
    print("========================================================")

    try:
        # Use subprocess.run to execute the command and redirect output
        with open(output_file, 'w') as out_file:
            process = subprocess.run(
                ping_cmd,
                stdout=out_file,
                stderr=subprocess.STDOUT,
                check=True
            )
        print("====== PING Completed Successfully ======")
        logging.info(f"Ping Test Successful - {corenet_name}")
        return True
    except subprocess.CalledProcessError as e:
        print("====== PING Failed ======")
        logging.error(f"Ping Test Failed - {corenet_name}: {str(e)}")
        return False
    except Exception as e:
        print(f"====== PING Error: {str(e)} ======")
        logging.error(f"Ping Test Error: {str(e)}")
        return False


def iperf_tcp_test(
    server_ip: str,
    interface_ip: str,
    port: int = 5201,
    output_file: str = "./test/iperf_tcp.txt",
    corenet_name: str = "",
    duration: int = 120,
    interval: int = 5,
) -> bool:
    """
    Server: iperf -s -p 5201
    Client: iperf -c [SERVER_IP] -p 5201 -t 120 -i 5 --bind [UESIMTUN0_IP] > ./test/iperf_tcp.txt 2>&1

    Args:
        server_ip: Server IP address (free5gc VM, for test)
        interfaceIP: net interface ip, default uesimtun0 (10.45.0.2 / 10.42.0.2)
        output_file: output file path
        corenet_name: corenet name, for logging

    Return:
        bool: True if iperf is successful, False otherwise
    """

    logging.info(f"iperf Test (TCP): Connecting to {server_ip} "
                f"via {corenet_name if corenet_name else interface_ip}...")
    ensure_dir(output_file)
    iperf_cmd = [
        "sudo",
        "iperf",
        "-c", server_ip,
        "-p", str(port),
        "-t", str(duration),
        "-i", str(interval),
        "--bind", interface_ip,
    ]

    print("========================================================")
    print(f"=== iPerf TCP Test {server_ip} via {corenet_name} ===")
    print("========================================================")

    try:
        # Use subprocess.run to execute the command and redirect output
        with open(output_file, 'w') as out_file:
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


def iperf_udp_test(
    server_ip: str,
    interface_ip: str,
    port: int = 5001,
    output_file: str = "./test/iperf_udp.txt",
    corenet_name: str = "",
    duration: int = 120,
    interval: int = 5,
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
    ensure_dir(output_file)
    iperf_cmd = [
        "sudo",
        "iperf",
        "-u", 
        "-c", server_ip,
        "-p", str(port),
        "-t", str(duration),
        "-i", str(interval),
        "--bind", interface_ip,
    ]

    print("========================================================")
    print(f"=== iPerf UDP Test {server_ip} via {corenet_name} ===")
    print("========================================================")

    try:
        # Use subprocess.run to execute the command and redirect output
        with open(output_file, 'w') as out_file:
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
