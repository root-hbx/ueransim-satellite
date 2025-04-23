import os
import re
import matplotlib.pyplot as plt

BW_MAX = 200 # Mbps

all_datas = []
std_times = []
std_thps = []

def process_data():
    for i in range(len(std_times)):
        thor_total_data = std_times[i] * BW_MAX # Mb
        thor_total_data = thor_total_data / 8 # MB
        std_thps.append(all_datas[i] / thor_total_data) # link utilization rate


for filename in os.listdir('../std'):
    if filename.startswith('continuous_tcp_traffic_') and filename.endswith('.txt'):
        filepath = os.path.join('../std', filename)

        with open(filepath, 'r') as file:
            content = file.read()

            # total_data_match = re.search(r'Total Data: (\d+\.\d+)', content)
            total_data_match = re.search(r'Total Data: (\d+)', content)
            if total_data_match:
                data = float(total_data_match.group(1))
                all_datas.append(data)

            total_time_match = re.search(r'TCP Runtime: (\d+\.\d+)', content)
            if total_time_match:
                time = float(total_time_match.group(1))
                std_times.append(time)

if len(all_datas) != len(std_times):
    print("All Data Transferred:", all_datas)
    print("Divided Link UtiRate", std_times)
else:
    process_data()

    fig, ax1 = plt.subplots(figsize=(10, 6))

    sorted_data = sorted(zip(std_times, all_datas, std_thps))
    sorted_times, sorted_datas, sorted_thps = zip(*sorted_data)

    # t - Data Transfer
    color = 'tab:blue'
    ax1.set_xlabel('Time for TCP (s)')
    ax1.set_ylabel('Data Transfer (MB)', color=color)
    line1 = ax1.plot(sorted_times, sorted_datas, marker='o', linestyle='-', color=color, label='Data Transfer')
    ax1.tick_params(axis='y', labelcolor=color)

    # t - Link Utilization Rate
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Link Utilization Rate', color=color)
    line2 = ax2.plot(sorted_times, sorted_thps, marker='s', linestyle='--', color=color, label='Link Utilization Rate')
    ax2.tick_params(axis='y', labelcolor=color)

    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='best')
    ax1.grid(True, linestyle='--', alpha=0.7)
    plt.title('TCP Performance Analysis')
    
    fig.tight_layout()
    plt.savefig('../image/std_tcp_performance.png', dpi=300)
