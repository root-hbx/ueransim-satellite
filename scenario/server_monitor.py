import os
import subprocess
import logging

"""
This script should be run on free5gc machine
"""

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)


def start_tcp_server(
    output_file="./test/iperf_tcp_server.txt",
    port=5201
) -> subprocess.Popen:
    """
    iperf -s -p 5201 > ./test/iperf_tcp_server.txt
    """
    ensure_dir(output_file)
    cmd = ["iperf", "-s", "-p", str(port)]

    print("========================================================")
    logging.info(f"TCP iPerf Server Start Monitoring: {output_file}")
    logging.info(f"TCP iPerf Server Port: {port}")
    print("========================================================")

    with open(output_file, 'w') as out_file:
        process = subprocess.Popen(
            cmd,
            stdout=out_file,
            stderr=subprocess.STDOUT
        )

    return process


def start_udp_server(
    output_file="./test/iperf_udp_server.txt",
    port=5001
) -> subprocess.Popen:
    """
    iperf -u -s -p 5001 > ./test/iperf_udp_server.txt
    """
    ensure_dir(output_file)
    cmd = ["iperf", "-s", "-u", "-p", str(port)]

    print("========================================================")
    logging.info(f"UDP iPerf Server Start Monitoring: {output_file}")
    logging.info(f"UDP iPerf Server Port: {port}")
    print("========================================================")

    with open(output_file, 'w') as out_file:
        process = subprocess.Popen(
            cmd,
            stdout=out_file,
            stderr=subprocess.STDOUT
        )

    return process


def stop_server(process):
    if process and process.poll() is None:
        process.terminate()
        print(f"Server Process Terminated (PID = {process.pid}).")


if __name__ == "__main__":

    tcp_process = start_tcp_server()
    udp_process = start_udp_server()

    try:
        tcp_process.wait()
        udp_process.wait()
    except KeyboardInterrupt:
        logging.info("Server stopped by user...")
        stop_server(tcp_process)
        stop_server(udp_process)
        logging.info("All iPerf Server Processes Terminated :)")

