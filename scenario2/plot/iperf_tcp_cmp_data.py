import os
import re
import matplotlib.pyplot as plt

BW_MAX = 200  # Mbps

def check_data_validity(folder_name, tcp_times, theo_datas, actual_datas, link_util_rates):
    print(f"--- {folder_name} Folder Data ---")
    print("Time points:", len(tcp_times))
    print("Theoretical data points:", len(theo_datas))
    print("Actual data points:", len(actual_datas))
    print("Link utilization rate points:", len(link_util_rates))
    print()

    if len(tcp_times) != len(link_util_rates):
        print(f"Warning: Data length mismatch in {folder_name} folder")
        return False
    return True

def extract_data_from_folder_test(folder_path):
    tcp_times = []
    theo_datas = []
    actual_datas = []
    link_util_rates = []

    for filename in os.listdir(folder_path):
        if filename.startswith('continuous_tcp_traffic_') and filename.endswith('.txt'):
            filepath = os.path.join(folder_path, filename)

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

                for match in mb_data_matches:
                    mb_value = float(match)
                    all_mb_values.append(mb_value)

                all_mb_values.sort(reverse=True)
                total_mb_value = sum(all_mb_values[:2]) if len(all_mb_values) >= 2 else sum(all_mb_values)

                if total_mb_value > 0:
                    actual_datas.append(total_mb_value)

    if len(theo_datas) == len(actual_datas):
        for i in range(len(theo_datas)):
            link_util_rates.append(actual_datas[i] / theo_datas[i])

    return tcp_times, theo_datas, actual_datas, link_util_rates

def extract_data_from_folder_std(folder_path):
    tcp_times = []
    theo_datas = []
    actual_datas = []
    link_util_rates = []
    
    for filename in os.listdir(folder_path):
        if filename.startswith('continuous_tcp_traffic_') and filename.endswith('.txt'):
            filepath = os.path.join(folder_path, filename)

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

                for match in mb_data_matches:
                    mb_value = float(match)
                    all_mb_values.append(mb_value)

                all_mb_values.sort(reverse=True)
                total_mb_value = all_mb_values[0]

                if total_mb_value > 0:
                    actual_datas.append(total_mb_value)

    if len(theo_datas) == len(actual_datas):
        for i in range(len(theo_datas)):
            link_util_rates.append(actual_datas[i] / theo_datas[i])

    return tcp_times, theo_datas, actual_datas, link_util_rates


test_tcp_times, test_theo_datas, test_actual_datas, test_link_util_rates = extract_data_from_folder_test('../test')
std_tcp_times, std_theo_datas, std_actual_datas, std_link_util_rates = extract_data_from_folder_std('../std')

test_valid = check_data_validity("Test", test_tcp_times, test_theo_datas, test_actual_datas, test_link_util_rates)
std_valid = check_data_validity("Std", std_tcp_times, std_theo_datas, std_actual_datas, std_link_util_rates)

assert test_valid and std_valid, print("Could not create plot due to data validity issues")

fig, ax = plt.subplots(figsize=(10, 6))

sorted_test_data = sorted(zip(test_tcp_times, test_link_util_rates))
sorted_test_times = [x[0] for x in sorted_test_data]
sorted_test_util_rates = [x[1] for x in sorted_test_data]

sorted_std_data = sorted(zip(std_tcp_times, std_link_util_rates))
sorted_std_times = [x[0] for x in sorted_std_data]
sorted_std_util_rates = [x[1] for x in sorted_std_data]

ax.scatter(sorted_test_times, sorted_test_util_rates, color='tab:red', label='Test Link Utilization')
ax.plot(sorted_test_times, sorted_test_util_rates, color='tab:red', linestyle='-', linewidth=1.5)

ax.scatter(sorted_std_times, sorted_std_util_rates, color='tab:blue', label='Standard Link Utilization')
ax.plot(sorted_std_times, sorted_std_util_rates, color='tab:blue', linestyle='-', linewidth=1.5)

ax.set_xlabel('TCP Transmitted Time (s)')
ax.set_ylabel('Link Utilization Rate')
ax.set_ylim(0, 1)
ax.grid(True)
ax.legend(loc='best')

plt.title('Comparison of Link Utilization Rates')
fig.tight_layout()
plt.savefig('../image/iperf_tcp_comparison.png', dpi=300)
print("Plot saved to '../image/iperf_tcp_comparison.png'")

