import os
import re
import matplotlib.pyplot as plt

BW_MAX = 200 # Mbps

tcp_times = []
theo_datas = []
actual_datas = []
link_util_rates = []

def process_data():
    for i in range(len(theo_datas)):
        link_util_rates.append(actual_datas[i] / theo_datas[i]) # link utilization rate


for filename in os.listdir('../test'):
    if filename.startswith('continuous_tcp_traffic_') and filename.endswith('.txt'):
        filepath = os.path.join('../test', filename)

        with open(filepath, 'r') as file:
            content = file.read()

            tcp_time_match = re.search(r'Total TCP Time: (\d+\.\d+)', content)
            if tcp_time_match:
                time = float(tcp_time_match.group(1))
                tcp_times.append(time)
                
            theo_data_match = re.search(r'All Data Generated: (\d+\.\d+)', content)
            if theo_data_match:
                data = float(theo_data_match.group(1))
                theo_datas.append(data)

            gb_data_matches = re.findall(r'\[\s*\d+\]\s*0\.0-\d+\.\d+\s*sec\s*(\d+\.\d+)\s*GBytes', content)
            mb_data_matches = re.findall(r'\[\s*\d+\]\s*0\.0-\d+\.\d+\s*sec\s*(\d+(?:\.\d+)?)\s*MBytes', content)

            total_mb_value = 0
            for match in gb_data_matches:
                gb_value = float(match)
                mb_value = gb_value * 1024
                total_mb_value += mb_value
            
            for match in mb_data_matches:
                mb_value = float(match)
                total_mb_value += mb_value

            if total_mb_value > 0:
                actual_datas.append(total_mb_value)
                print(f"File: {filename}, Total TCP Data Received (MB): {total_mb_value}")


if len(tcp_times) != len(theo_datas) or len(tcp_times) != len(actual_datas) or len(theo_datas) != len(actual_datas):
    print("TimeFlow (s):", tcp_times)
    print("Theoretical TCP Data (MB):", theo_datas)
    print("Actual Received Data (MB):", actual_datas)
else:
    process_data()

    plt.figure(figsize=(10, 6))

    sorted_data = sorted(zip(tcp_times, actual_datas, link_util_rates))
    sorted_tcp_times = [x[0] for x in sorted_data]
    sorted_actual_datas = [x[1] for x in sorted_data]
    sorted_link_util_rates = [x[2] for x in sorted_data]

    # scatter for single point
    plt.scatter(sorted_tcp_times, sorted_actual_datas, color='red', label='Theoretical')
    plt.scatter(sorted_tcp_times, sorted_link_util_rates, color='green', label='Actual')

    # plot for line
    plt.plot(sorted_tcp_times, sorted_actual_datas, color='red', linestyle='-', linewidth=1.5)
    plt.plot(sorted_tcp_times, sorted_link_util_rates, color='green', linestyle='-', linewidth=1.5)

    plt.xlabel('TCP Transmitted Time (s)')
    plt.ylabel('Link Utilization Rate')
    plt.title('Switching: Link Utilization && Actual Data Transferred')
    plt.grid(True)
    plt.legend() # show legend
    # plt.show()
    plt.savefig('../image/iperf_tcp_test.png', dpi=300)
