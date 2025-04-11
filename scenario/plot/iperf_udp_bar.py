import os
import re
import matplotlib.pyplot as plt
import numpy as np

udp_rates = []
all_costs = []
roaming_costs = []

for filename in os.listdir('../test'):
    if filename.startswith('continuous_udp_traffic_') and filename.endswith('.txt'):
        filepath = os.path.join('../test', filename)

        with open(filepath, 'r') as file:
            content = file.read()

            udp_rate_match = re.search(r'(\d+(?:\.\d+)?)\s*Mbits/sec', content)
            if udp_rate_match:
                udp_rate = float(udp_rate_match.group(1))
                udp_rates.append(udp_rate)

            all_cost_match = re.search(r't_all_cost = (\d+\.\d+)', content)
            if all_cost_match:
                all_cost = float(all_cost_match.group(1))
                all_costs.append(all_cost)

            roaming_cost_match = re.search(r't_roaming_cost = (\d+\.\d+)', content)
            if roaming_cost_match:
                roaming_cost = float(roaming_cost_match.group(1))
                roaming_costs.append(roaming_cost)

if len(udp_rates) != len(all_costs) or len(udp_rates) != len(roaming_costs) or len(all_costs) != len(roaming_costs):
    print("Mismatch between UDP rates and all costs.")
    print("UDP rates:", udp_rates)
    print("All costs:", all_costs)
    print("Roaming costs:", roaming_costs)
else:
    plt.figure(figsize=(12, 7))

    sorted_data = sorted(zip(udp_rates, all_costs, roaming_costs))
    sorted_udp_rates = [x[0] for x in sorted_data]
    sorted_all_costs = [x[1] for x in sorted_data]
    sorted_roaming_costs = [x[2] for x in sorted_data]

    x = np.arange(len(sorted_udp_rates))
    width = 0.35  # 条形图宽度

    plt.bar(x - width/2, sorted_all_costs, width, color='deepskyblue', label='t_all_cost')
    plt.bar(x + width/2, sorted_roaming_costs, width, color='orange', label='t_roaming_cost')
    
    plt.xticks(x, [f"{rate}" for rate in sorted_udp_rates], rotation=45 if len(sorted_udp_rates) > 8 else 0)
    
    plt.xlabel('UDP Bandwidth (Mbps)')
    plt.ylabel('Time Cost (s)')
    plt.title('UDP Bandwidth vs. Time Cost')
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    
    # plt.show()
    plt.savefig('../image/iperf_udp_bar.png', dpi=300)