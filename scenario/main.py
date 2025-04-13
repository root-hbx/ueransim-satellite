import os
import subprocess
import time
import sys
import logging
import threading
import signal
import traceback
from network_sim import (
    get_uesimtun0_ip,
    wait_for_uesimtun0_ip,
    iperf_tcp_test
)

"""
This script should be run on UERANSIM machine
"""

# Pls replace with your own path
ROOT_DIR = "/home/ueransim/ueransim-satellite"
FREE5GC_IP = "172.16.162.135"
BW4TCP = "1G"

logging.basicConfig(level=logging.INFO)

"""
Flow:
- 0-70s: Continuous TCP background traffic flow 
  * 0-35s: Through open5gs-1 (10.45.0.2)
  * 35-70s: Through open5gs-2 (10.42.0.2)
"""

# 全局变量用于控制和共享状态
current_interface_ip = None
iperf_process = None
interface_changed_event = threading.Event()
stop_monitoring = threading.Event()
TOTAL_DATA = "40G"  # 总共需要传输的数据量

def admin():
    """
    Check for sudo at first
    """
    print("=====================================================")
    print("== Authentication: Checking for sudo Permission ==")
    print("=====================================================")

    try:
        result = subprocess.run(
            ["sudo", "-v"], 
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("Passed! Now we are good :)")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Invalid Permissions: {e}")
        print("Failed! Plz check for your password as a root admin :(")
        sys.exit(1)


def terminate_processes(
    gnb_process: subprocess.Popen, 
    ue_process: subprocess.Popen
) -> None:
    """Terminate gNB and UE processes by Force && Clear uesimtun0 Network Interface"""
    if gnb_process:
        try:
            gnb_process.kill()
            logging.info("gNB process has been forcefully killed")
        except Exception as e:
            logging.error(f"Error killing gNB process: {e}")

    if ue_process:
        try:
            subprocess.run(["sudo", "pkill", "-f", "nr-ue"], check=True)
            logging.info("UE process has been forcefully killed")
        except Exception as e:
            logging.error(f"Error killing UE process: {e}")


def start_gnb(
    config_file: str) -> subprocess.Popen:
    """Start gNB with the given configuration file"""
    logging.info("Starting gNB...")
    gnb_cmd = [
        os.path.join(ROOT_DIR, "build/nr-gnb"),
        "-c",
        os.path.join(ROOT_DIR, config_file)
    ]
    gnb_process = subprocess.Popen(gnb_cmd, cwd=ROOT_DIR)
    logging.info(f"gNB process started (PID: {gnb_process.pid})")
    return gnb_process


def start_ue(
    config_file: str) -> subprocess.Popen:
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
    return ue_process


def monitor_uesimtun0_interface():
    """持续监控uesimtun0接口的变化"""
    global current_interface_ip, iperf_process
    
    logging.info("开始监控uesimtun0接口...")
    
    while not stop_monitoring.is_set():
        try:
            new_ip = get_uesimtun0_ip()
            
            if new_ip:
                # 如果IP发生变化
                if new_ip != current_interface_ip and current_interface_ip is not None:
                    logging.info(f"接口IP变化检测: 从 {current_interface_ip} 到 {new_ip}")
                    current_interface_ip = new_ip
                    interface_changed_event.set()  # 触发接口变化事件
                elif current_interface_ip is None:
                    current_interface_ip = new_ip
                    logging.info(f"初始接口IP: {current_interface_ip}")
            else:
                if current_interface_ip is not None:
                    logging.info("未检测到接口IP，可能已断开连接")
                    interface_changed_event.set()  # 触发接口变化事件
                    current_interface_ip = None
        except Exception as e:
            logging.error(f"监控uesimtun0接口时出错: {e}")
            if current_interface_ip is not None:
                logging.info("uesimtun0接口可能不存在")
                current_interface_ip = None
                interface_changed_event.set()  # 触发接口变化事件

        # 每秒检查一次
        time.sleep(0.1)


def run_scenario():
    """Constructing the scenario with time-controlled connections"""
    global BW4TCP, current_interface_ip, iperf_process, stop_monitoring

    output_file = f"./test/continuous_tcp_traffic_{BW4TCP}.txt"

    gnb1_process = None
    ue1_process = None
    gnb2_process = None
    ue2_process = None
    
    try:
        # Create a daemon thread to monitor the uesimtun0 interface
        # Real-time monitoring of the uesimtun0 interface (for switching)
        monitor_thread = threading.Thread(target=monitor_uesimtun0_interface, daemon=True)
        monitor_thread.start()

        # Start Time of Phase 1
        start_time = time.time()

        # [Phase 1] Connecting with open5gs-1
        logging.info("[t=0] Connecting with Open5GS-1...")
        gnb1_process = start_gnb("config/open5gs1-gnb.yaml")
        ue1_process = start_ue("config/open5gs1-ue.yaml")

        [interface1_ip, built1_probe] = wait_for_uesimtun0_ip(max_attempts=10, delay=1)
        current_interface_ip = interface1_ip

        # TCP Traffic Gen (One-Time, 40G)
        logging.info(f"[t={built1_probe - start_time}] TCP Traffic Generation ({interface1_ip})")
        with open(output_file, "a") as f:
            f.write(f"TCP Traffic Total Data: {TOTAL_DATA}\n")
            f.write(f"[t={built1_probe - start_time}] TCP Traffic Generation ({interface1_ip})")

        # Create TCP BGD Traffic, as a new thread
        iperf_thread = threading.Thread(
            target=iperf_tcp_test,
            args=(FREE5GC_IP, interface1_ip),
            kwargs={
                "port": 5201,
                "output_file": output_file,
                "corenet_name": "open5gs-1 & open5gs-2",
                "totaldata": TOTAL_DATA,  # 总共40G
                "interval": 1,
                "bandwidth": BW4TCP
            },
            daemon=True
        )
        iperf_thread.start()

        # Maintain the connection for 25 seconds
        logging.info("Connecting with Open5GS-1 for 25 seconds...")
        time.sleep(25)

        # End of Phase 1
        logging.info("Terminating the Connection with Open5GS-1...")
        terminate_processes(gnb1_process, ue1_process)
        gnb1_process = None
        ue1_process = None

        '''
        ==========================================================
        '''

        # Start Time of Phase 2
        phase2_time = time.time() - start_time

        # [Phase 2] Connecting with open5gs-2
        logging.info(f"[t = {phase2_time}] Connecting with Open5GS-2...")
        gnb2_process = start_gnb("config/open5gs2-gnb.yaml")
        ue2_process = start_ue("config/open5gs2-ue.yaml")

        # Waiting for Interface Switching
        interface_changed_event.wait(timeout=20)
        interface_changed_event.clear()

        # Get New Interface IP
        if current_interface_ip:
            [interface2_ip, built2_probe] = wait_for_uesimtun0_ip(max_attempts=10, delay=1)
            assert interface2_ip == current_interface_ip, "Interface IP mismatch"

            with open(output_file, "a") as f:
                f.write(f"[t={built2_probe - start_time}] TCP Traffic Generation ({interface2_ip})")
                f.write("TCP Traffic Transmission Continues...\n")

            # 注意：在现有实现中，iperf_tcp_test会在接口不可用时自然终止
            # 当接口重新可用后，数据传输会继续但可能需要重新启动
            # 这里我们等待iperf线程完成
            iperf_thread.join(timeout=60)
        else:
            logging.error("Could not fetch the new interface IP...")

    except Exception as e:
        logging.error(f"Error: {e}")
        logging.error(traceback.format_exc())
    finally:
        stop_monitoring.set()
        
        if gnb1_process or ue1_process:
            logging.info("Terminating the Connection with Open5GS-1...")
            terminate_processes(gnb1_process, ue1_process)

        if gnb2_process or ue2_process:
            logging.info("Terminating the Connection with Open5GS-2...")
            terminate_processes(gnb2_process, ue2_process)

        logging.info(f"Outputs are stored into: {output_file}")
        logging.info("TCP Scenario completed!")


if __name__ == "__main__":
    admin()

    # Default
    BW4TCP = "1G"
    run_scenario()
    time.sleep(3)

    # # Different bandwidth
    # for i in range(10, 310, 10):
    #     bw = f"{i}M"
    #     try:
    #         BW4TCP = bw
    #         run_scenario()
    #     except Exception as e:
    #         logging.error(f"Error during test with bandwidth {bw}: {e}")
    #     finally:
    #         time.sleep(3)
