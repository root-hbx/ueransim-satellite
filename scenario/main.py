import os
import subprocess
import time
import signal
import sys

ROOT_DIR = "/Users/huluobo/Github_Content/ueransim-satellite"

def run_scenario():
    print("开始场景模拟...")

    # 创建两个进程组
    gnb_process = None
    ue_process = None

    # 第一阶段：连接 open5gs1 (1分钟)
    print("\n=== 阶段1：连接 open5gs1 ===")
    
    # 启动 gNB
    print("启动 gNB...")
    gnb_cmd = [
        os.path.join(ROOT_DIR, "build/nr-gnb"),
        "-c",
        os.path.join(ROOT_DIR, "config/open5gs-gnb.yaml")
    ]
    gnb_process = subprocess.Popen(gnb_cmd, cwd=ROOT_DIR)
    print(f"gNB 进程已启动 (PID: {gnb_process.pid})")
    
    # 等待 gNB 启动完成
    time.sleep(2)
    
    # 启动 UE
    print("启动 UE...")
    ue_cmd = [
        "sudo",
        os.path.join(ROOT_DIR, "build/nr-ue"),
        "-c",
        os.path.join(ROOT_DIR, "config/open5gs-ue.yaml")
    ]
    ue_process = subprocess.Popen(ue_cmd, cwd=ROOT_DIR)
    print(f"UE 进程已启动 (PID: {ue_process.pid})")
    
    #TODO(bxhu): add `ping -I uersimtun0 192.168.0.1` via open5gs1

    # 等待2分钟
    print("等待2分钟, 此时跟open5gs1进行交互...")
    time.sleep(120)

    # 终止第一阶段的进程
    if gnb_process:
        gnb_process.terminate()
        gnb_process.wait(timeout=5)
        print("gNB 进程已终止")
        
    if ue_process:
        os.system(f"sudo kill {ue_process.pid}")
        print("UE 进程已终止")




    # 第二阶段：连接 open5gs2
    print("\n=== 阶段2：连接 open5gs2 ===")
    
    # 启动 gNB
    print("启动 gNB...")
    gnb_cmd = [
        os.path.join(ROOT_DIR, "build/nr-gnb"),
        "-c",
        os.path.join(ROOT_DIR, "config/open5gs2-gnb.yaml")
    ]
    gnb_process = subprocess.Popen(gnb_cmd, cwd=ROOT_DIR)
    print(f"gNB 进程已启动 (PID: {gnb_process.pid})")
    
    # 等待 gNB 启动完成
    time.sleep(2)
    
    # 启动 UE
    print("启动 UE...")
    ue_cmd = [
        "sudo",
        os.path.join(ROOT_DIR, "build/nr-ue"),
        "-c",
        os.path.join(ROOT_DIR, "config/open5gs2-ue.yaml")
    ]
    ue_process = subprocess.Popen(ue_cmd, cwd=ROOT_DIR)
    print(f"UE 进程已启动 (PID: {ue_process.pid})")

    #TODO(bxhu): add `ping -I uersimtun0 192.168.0.1` via open5gs2

    # 等待2分钟
    print("等待2分钟, 此时跟open5gs2进行交互...")
    time.sleep(120)
    
    # 终止第一阶段的进程
    if gnb_process:
        gnb_process.terminate()
        gnb_process.wait(timeout=5)
        print("gNB 进程已终止")
        
    if ue_process:
        os.system(f"sudo kill {ue_process.pid}")
        print("UE 进程已终止")



if __name__ == "__main__":
    run_scenario()
