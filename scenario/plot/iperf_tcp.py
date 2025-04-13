import os
import re
import glob
import matplotlib.pyplot as plt
import numpy as np

def extract_data_from_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    # 将文件内容分成两个连接段
    connections = content.split("------------------------------------------------------------\nClient connecting")
    if len(connections) > 1:
        connections = ["Client connecting" + conn for conn in connections[1:]]

    results = []
    for conn in connections:
        # 提取TCP速率
        bw_match = re.search(r"(\d+\.\d+) Gbits/sec", conn)
        if bw_match:
            tcp_rate = float(bw_match.group(1))
        else:
            continue

        # 提取总结行
        summary_match = re.search(r"\[\s*\d+\]\s+(\d+\.\d+)-(\d+\.\d+)\s+sec\s+(\d+\.\d+)\s+(\w+)\s+(\d+\.\d+)\s+Gbits/sec$", conn, re.MULTILINE)
        if summary_match:
            start_time = float(summary_match.group(1))
            end_time = float(summary_match.group(2))
            transfer = float(summary_match.group(3))
            transfer_unit = summary_match.group(4)
            # 转换为GBytes统一单位
            if transfer_unit == "MBytes":
                transfer = transfer / 1024
            time_span = end_time - start_time

            results.append({
                'tcp_rate': tcp_rate,
                'time_span': time_span,
                'transfer': transfer
            })

    return results

def main():
    file_pattern = "../test/continuous_tcp_traffic_*.txt"
    files = glob.glob(file_pattern)

    if not files:
        print(f"No files found matching pattern: {file_pattern}")
        return

    tcp_rates = []
    utilization_rates = []

    for file_path in files:
        results = extract_data_from_file(file_path)
        
        if len(results) >= 2:
            tcp_rate = results[0]['tcp_rate']  # 假设两个连接的TCP速率相同
            
            # 计算链路利用率: (X + Y) / (a*b + c*d)
            total_transfer = results[0]['transfer'] + results[1]['transfer']
            total_capacity = (results[0]['time_span'] * results[0]['tcp_rate'] + 
                             results[1]['time_span'] * results[1]['tcp_rate'])
            
            # GBytes / (seconds * Gbits/sec) = GBytes / (Gbits) = 8
            # 需要转换单位: 1 GByte = 8 Gbits
            utilization = (total_transfer * 8) / total_capacity
            
            tcp_rates.append(tcp_rate)
            utilization_rates.append(utilization)
            
            print(f"File: {os.path.basename(file_path)}")
            print(f"TCP Rate: {tcp_rate} Gbits/sec")
            print(f"Link Utilization: {utilization:.4f}")
            print("-" * 30)

    plt.figure(figsize=(10, 6))
    plt.scatter(tcp_rates, utilization_rates, s=50, alpha=0.7, c='blue', edgecolors='black')

    if tcp_rates:
        z = np.polyfit(tcp_rates, utilization_rates, 1)
        p = np.poly1d(z)
        plt.plot(sorted(tcp_rates), p(sorted(tcp_rates)), 'r--', linewidth=2)

    plt.xlabel('TCP Rate (Gbits/sec)')
    plt.ylabel('Link Utilization')
    plt.title('TCP Link Utilization vs. TCP Rate')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../image/tcp_link_utilization.png', dpi=300)
    plt.show()

if __name__ == "__main__":
    os.makedirs('../image', exist_ok=True)
    main()
