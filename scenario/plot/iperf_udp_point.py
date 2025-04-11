import os
import re
import matplotlib.pyplot as plt

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
                
            roaming_cost_match = re.match(r't_roaming_cost = (\d+\.\d+)', content)
            if roaming_cost_match:
                roaming_cost = float(roaming_cost_match.group(1))
                roaming_costs.append(roaming_cost)

if len(udp_rates) != len(all_costs) or len(udp_rates) != len(roaming_costs) or len(all_costs) != len(roaming_costs):
    print("Mismatch between UDP rates and all costs.")
    print("UDP rates:", udp_rates)
    print("All costs:", all_costs)
    print("Roaming costs:", roaming_costs)
else:
    plt.figure(figsize=(10, 6))
    plt.scatter(udp_rates, all_costs, color='red', label='t_all_cost')
    plt.scatter(udp_rates, roaming_costs, color='green', label='t_roaming_cost')

    plt.xlabel('UDP Bandwidth (Mbps)')
    plt.ylabel('Time Cost (s)')
    plt.title('UDP Bandwidth vs. Time Cost')
    plt.grid(True)
    # plt.show()
    plt.savefig('../image/iperf_udp_point.png', dpi=300) # create image/ manually
