import os
import subprocess
import time
import sys
import logging
import threading
import signal
from network_sim import (
    get_uesimtun0_ip,
    wait_for_uesimtun0_ip,
    ensure_dir,
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
total_data = "40G"  # 总共需要传输的数据量

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
        time.sleep(1)


def run_iperf_tcp_background(server_ip, interface_ip, port, output_file, corenet_name, bandwidth):
    """运行持续的TCP背景流量测试"""
    global iperf_process
    
    logging.info(f"启动TCP背景流通过接口 {interface_ip} 连接到 {corenet_name}")
    
    # 如果已经有一个iperf进程在运行，先终止它
    if iperf_process and iperf_process.poll() is None:
        try:
            os.killpg(os.getpgid(iperf_process.pid), signal.SIGTERM)
            iperf_process.wait()
        except Exception as e:
            logging.error(f"终止先前的iperf进程时出错: {e}")
    
    with open(output_file, "a") as f:
        f.write(f"[{time.time()}] 启动通过 {corenet_name} ({interface_ip}) 的TCP流量\n")
    
    # 使用iperf3而不是iperf命令
    iperf_cmd = [
        "iperf3", 
        "-c", server_ip, 
        "-B", interface_ip,
        "-p", str(port),
        "-i", "1",     # 每秒报告一次
        "-t", "3600",  # 运行足够长的时间
        "-b", bandwidth,
        "-n", total_data,  # 总共传输40G数据
    ]
    
    logging.info(f"运行命令: {' '.join(iperf_cmd)}")
    
    # 使用新进程组启动iperf，便于稍后终止
    iperf_process = subprocess.Popen(
        iperf_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        preexec_fn=os.setpgrp  # 使用新的进程组
    )
    
    # 启动线程读取并记录iperf输出
    def log_output():
        with open(output_file, "a") as f:
            while iperf_process.poll() is None:
                line = iperf_process.stdout.readline()
                if line:
                    f.write(f"[{time.time()}] {line}")
                    f.flush()
    
    threading.Thread(target=log_output, daemon=True).start()


def run_scenario():
    """Constructing the scenario with time-controlled connections"""
    global BW4TCP, current_interface_ip, iperf_process, stop_monitoring

    output_file = f"./test/continuous_tcp_traffic_{BW4TCP}.txt"

    gnb1_process = None
    ue1_process = None
    gnb2_process = None
    ue2_process = None
    
    # 发送的数据计数器
    data_transferred = 0
    
    try:
        monitor_thread = threading.Thread(target=monitor_uesimtun0_interface, daemon=True)
        monitor_thread.start()
        
        # 记录开始时间作为时间戳0
        start_time = time.time()
        logging.info(f"[t=0] 连接到open5gs-1...")
        
        # 1. 开始连接到open5gs-1
        gnb1_process = start_gnb("config/open5gs1-gnb.yaml")
        ue1_process = start_ue("config/open5gs1-ue.yaml")

        interface1_ip, built1_probe = wait_for_uesimtun0_ip(max_attempts=10, delay=1)
        current_interface_ip = interface1_ip
        
        # 启动TCP背景流，只启动一次，发送40G数据
        logging.info(f"启动TCP背景流传输总共{total_data}数据")
        with open(output_file, "a") as f:
            f.write(f"[{time.time()}] 启动通过 open5gs-1 ({interface1_ip}) 的TCP流量，总量{total_data}\n")
        
        # 使用network_sim中的iperf_tcp_test函数启动背景流
        # 使用新线程启动iperf_tcp_test，这样不会阻塞主线程
        iperf_thread = threading.Thread(
            target=iperf_tcp_test,
            args=(FREE5GC_IP, interface1_ip),
            kwargs={
                "port": 5201,
                "output_file": output_file,
                "corenet_name": "open5gs-1 & open5gs-2",
                "totaldata": total_data,  # 总共40G
                "interval": 1,
                "bandwidth": BW4TCP
            },
            daemon=True
        )
        iperf_thread.start()
        
        # 等待30秒后切换到open5gs-2
        logging.info("等待30秒后切换到open5gs-2...")
        time.sleep(30)
        
        # 2. 正确的切换方法: 先终止现有连接
        logging.info("先终止open5gs-1连接，再连接到open5gs-2...")
        terminate_processes(gnb1_process, ue1_process)
        gnb1_process = None
        ue1_process = None
        
        # 等待短暂时间确保旧连接完全释放
        time.sleep(2)
        
        # 记录接口断开
        with open(output_file, "a") as f:
            f.write(f"[{time.time() - start_time}] 网络切换中: 断开 open5gs-1 ({interface1_ip})\n")
        
        # 3. 然后启动到open5gs-2的新连接
        logging.info("启动到open5gs-2的连接...")
        gnb2_process = start_gnb("config/open5gs2-gnb.yaml")
        ue2_process = start_ue("config/open5gs2-ue.yaml")
        
        # 等待接口变化事件
        interface_changed_event.wait(timeout=20)
        interface_changed_event.clear()
        
        # 如果接口已变化，获取新IP
        if current_interface_ip:
            interface2_ip = current_interface_ip
            
            with open(output_file, "a") as f:
                f.write(f"[{time.time() - start_time}] 网络切换完成: 从 {interface1_ip} 到 {interface2_ip}\n")
                f.write(f"[{time.time() - start_time}] TCP流量继续通过 open5gs-2 ({interface2_ip}) 传输\n")
            
            logging.info(f"网络切换完成: 从 {interface1_ip} 到 {interface2_ip}")
            logging.info(f"TCP流量继续传输，直到完成总共{total_data}数据")
            
            # 注意：在现有实现中，iperf_tcp_test会在接口不可用时自然终止
            # 当接口重新可用后，数据传输会继续但可能需要重新启动
            # 这里我们等待iperf线程完成
            iperf_thread.join(timeout=600)  # 给足够时间完成传输，最多等待10分钟
            
        else:
            logging.error("无法获取open5gs-2的接口IP，TCP背景流切换失败")
        
    except Exception as e:
        logging.error(f"场景运行中出错: {e}")
        import traceback
        logging.error(traceback.format_exc())
    finally:
        stop_monitoring.set()
        
        if gnb1_process or ue1_process:
            terminate_processes(gnb1_process, ue1_process)
        
        if gnb2_process or ue2_process:
            terminate_processes(gnb2_process, ue2_process)

        logging.info(f"结果保存到 {output_file}")
        logging.info("场景成功完成")


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
