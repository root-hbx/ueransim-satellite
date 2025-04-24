import os
import re
import matplotlib.pyplot as plt

BW_MAX = 200 # Mbps

tcp_times = []
theo_datas = []
actual_datas = []
link_util_rates = []

def logging_msg(status: str):
    # log
    print("TimeFlow (s):", tcp_times)
    print("Length:", len(tcp_times))
    print()
    print("Theoretical TCP Data (MB):", theo_datas)
    print("Length:", len(theo_datas))
    print()
    print("Actual Received Data (MB):", actual_datas)
    print("Length:", len(actual_datas))
    print()
    if status == "error":
        print("Error: The length of the lists do not match.")
    else:
        print("Link Utilization Rate:", link_util_rates)
        print("Length:", len(link_util_rates))
        print()

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

            gb_data_matches = re.findall(r'\[\s*\d+\]\s*0\.0-\s*\d+\.\d+\s*sec\s*(\d+\.\d+)\s*GBytes', content)
            mb_data_matches = re.findall(r'\[\s*\d+\]\s*0\.0-\s*\d+\.\d+\s*sec\s+(\d+\.?\d*)\s*MBytes', content)

            all_mb_values = []
            for match in gb_data_matches:
                gb_value = float(match)
                mb_value = gb_value * 1024
                all_mb_values.append(mb_value)
                print(mb_value)

            for match in mb_data_matches:
                mb_value = float(match)
                all_mb_values.append(mb_value)
                print(mb_value)

            all_mb_values.sort(reverse=True)
            total_mb_value = sum(all_mb_values[:2]) if len(all_mb_values) >= 2 else sum(all_mb_values)

            if len(all_mb_values) >= 2:
                print(f"Taking top 2 values: {all_mb_values[0]}, {all_mb_values[1]}")
            elif len(all_mb_values) == 1:
                print(f"[Error] Taking the only 2 value: {all_mb_values[0]}")

            if total_mb_value > 0:
                actual_datas.append(total_mb_value)
                print(f"File: {filename}, Total TCP Data Received (MB): {total_mb_value}")
                print()
                # print(f"File: {filename}, Theoretical TCP Transfered (MB): {tho_data}")


if len(tcp_times) != len(theo_datas) or len(tcp_times) != len(actual_datas) or len(theo_datas) != len(actual_datas):
    # log
    logging_msg(status="error")
else:
    process_data()
    logging_msg(status="success")

    fig, ax1 = plt.subplots(figsize=(10, 6))

    sorted_data = sorted(zip(tcp_times, actual_datas, link_util_rates))
    sorted_tcp_times = [x[0] for x in sorted_data]
    sorted_actual_datas = [x[1] for x in sorted_data]
    sorted_link_util_rates = [x[2] for x in sorted_data]

    color1 = 'tab:red'
    ax1.set_xlabel('TCP Transmitted Time (s)')
    ax1.set_ylabel('Actual Data Transferred (MB)', color=color1)
    ax1.scatter(sorted_tcp_times, sorted_actual_datas, color=color1)
    ax1.plot(sorted_tcp_times, sorted_actual_datas, color=color1, linestyle='-', linewidth=1.5)
    ax1.tick_params(axis='y', labelcolor=color1)
    for x, y in zip(sorted_tcp_times, sorted_actual_datas):
        ax1.annotate(f'{y:.1f}', (x, y), textcoords="offset points", 
                    xytext=(0,10), ha='center', fontsize=8, color=color1)

    ax2 = ax1.twinx()
    color2 = 'tab:blue'
    ax2.set_ylabel('Link Utilization Rate', color=color2)
    ax2.scatter(sorted_tcp_times, sorted_link_util_rates, color=color2)
    ax2.plot(sorted_tcp_times, sorted_link_util_rates, color=color2, linestyle='-', linewidth=1.5)
    ax2.tick_params(axis='y', labelcolor=color2)
    ax2.set_ylim(0, 1)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, ['Actual Data'] + ['Link Utilization Rate'], loc='upper left')

    plt.title('Switching Flows: Link Utilization && Actual Data Transferred')
    plt.grid(True)
    fig.tight_layout()
    # plt.show()
    plt.savefig('../image/iperf_tcp_test.png', dpi=300)
