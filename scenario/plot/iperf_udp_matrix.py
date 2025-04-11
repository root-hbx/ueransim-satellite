import os
import re
import matplotlib.pyplot as plt
import numpy as np

udp_rates = []
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

            roaming_cost_match = re.search(r't_roaming_cost = (\d+\.\d+)', content)
            if roaming_cost_match:
                roaming_cost = float(roaming_cost_match.group(1))
                roaming_costs.append(roaming_cost)

if len(udp_rates) != len(roaming_costs):
    print("Mismatch between UDP rates and roaming costs.")
    print("UDP rates:", udp_rates)
    print("Roaming costs:", roaming_costs)
else:
    udp_ranges = np.arange(0, max(udp_rates) + 10, 10)  # define ranges from 0 to max rate + 10 Mbps
    labels = [f"{i}-{i+10} Mbps" for i in udp_ranges[:-1]]
    avg_roaming_costs = []

    for i in range(len(udp_ranges) - 1):
        range_costs = [cost for rate, cost in zip(udp_rates, roaming_costs) if udp_ranges[i] <= rate < udp_ranges[i+1]]
        if range_costs:
            avg_roaming_costs.append(np.mean(range_costs))
        else:
            avg_roaming_costs.append(0)

    plt.figure(figsize=(10, 6))
    plt.bar(labels, avg_roaming_costs)
    plt.xlabel('UDP Bandwidth Range (Mbps)')
    plt.ylabel('Average t_roaming_cost (s)')
    plt.title('UDP Bandwidth Range vs. Average Roaming Cost')
    plt.grid(True)
    plt.xticks(rotation=45)  # avoid overlapping labels
    plt.tight_layout()
    # plt.show()
    plt.savefig('../image/iperf_udp_matrix.png', dpi=300) # create image/ manually
