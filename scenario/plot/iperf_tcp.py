import os
import re
import matplotlib.pyplot as plt

BW_MAX = 200 # Mbps

all_datas = []
test_times = []
std_times = []

def process_data():
    for i in range(len(test_times)):
        test_times[i] = test_times[i] * BW_MAX # Mb
        test_times[i] = test_times[i] / 8 # MB
        test_times[i] = test_times[i] / 1024 # GB
        test_times[i] = all_datas[i] / test_times[i] # link utilization rate
    for i in range(len(std_times)):
        std_times[i] = std_times[i] * BW_MAX # Mb
        std_times[i] = std_times[i] / 8 # MB
        std_times[i] = std_times[i] / 1024 # GB
        std_times[i] = all_datas[i] / std_times[i] # link utilization rate


for filename in os.listdir('../test'):
    if filename.startswith('continuous_tcp_traffic_') and filename.endswith('.txt'):
        filepath = os.path.join('../test', filename)

        with open(filepath, 'r') as file:
            content = file.read()

            total_data_match = re.search(r'Total Data: (\d+)G', content)
            if total_data_match:
                data = float(total_data_match.group(1))
                all_datas.append(data)
                
            total_time_match = re.search(r'Total Time: (\d+\.\d+)', content)
            if total_time_match:
                time = float(total_time_match.group(1))
                test_times.append(time)

for filename in os.listdir('../std'):
    if filename.startswith('continuous_tcp_traffic_') and filename.endswith('.txt'):
        filepath = os.path.join('../std', filename)

        with open(filepath, 'r') as file:
            content = file.read()

            # total_data_match = re.search(r'Total Data: (\d+\.\d+)', content)
            # if total_data_match:
            #     data = float(total_data_match.group(1))
            #     all_datas.append(data)
                
            total_time_match = re.search(r'Total Time: (\d+\.\d+)', content)
            if total_time_match:
                time = float(total_time_match.group(1))
                std_times.append(time)

if len(all_datas) != len(test_times) or len(all_datas) != len(std_times) or len(std_times) != len(test_times):
    print("All Data Transferred:", all_datas)
    print("Divided Link UtiRate", test_times)
    print("One-Time Link UtiRate:", std_times)
else:
    process_data()

    plt.figure(figsize=(10, 6))

    sorted_data = sorted(zip(all_datas, test_times, std_times))
    sorted_all_datas = [x[0] for x in sorted_data]
    sorted_test_times = [x[1] for x in sorted_data]
    sorted_std_times = [x[2] for x in sorted_data]

    # scatter for single point
    plt.scatter(sorted_all_datas, sorted_test_times, color='red')
    plt.scatter(sorted_all_datas, sorted_std_times, color='green')

    # plot for line
    plt.plot(sorted_all_datas, sorted_test_times, color='red', linestyle='-', linewidth=1.5, label='Divided TCP (plot)')
    plt.plot(sorted_all_datas, sorted_std_times, color='green', linestyle='-', linewidth=1.5, label='One-Time TCP (plot)')

    plt.xlabel('TCP Transmitted Data (GB)')
    plt.ylabel('Link Utilization Rate')
    plt.title('One-Time TCP vs. Divided TCP [Original]')
    plt.grid(True)
    plt.legend() # show legend
    # plt.show()
    plt.savefig('../image/iperf_tcp_point_original.png', dpi=300) # create image/ manually
