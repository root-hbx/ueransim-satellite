import os
import re
import matplotlib.pyplot as plt

udp_rates = []
roaming_costs = []

for filename in os.listdir('../test'):
    if filename.startswith('continuous_udp_traffic_') and filename.endswith('.txt'):
        filepath = os.path.join('../test', filename)

        with open(filepath, 'r') as file:
            content = file.read()
            
            udp_rate_match = re.search(r'(\d+\.\d+) Mbits/sec', content)
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
    plt.figure(figsize=(10, 6))
    plt.scatter(udp_rates, roaming_costs)
    plt.xlabel('UDP Bandwidth (Mbps)')
    plt.ylabel('t_roaming_cost (s)')
    plt.title('UDP Bandwidth vs. Roaming Cost')
    plt.grid(True)
    plt.show()
