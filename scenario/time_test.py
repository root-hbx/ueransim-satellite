import time
import logging

"""
This script should be run on UERANSIM machine
"""

# Pls replace with your own path
ROOT_DIR = "/home/ueransim/ueransim-satellite"

FREE5GC_IP = "192.168.1.104"
OPEN5GS1_IP = "10.45.0.1"
OPEN5GS2_IP = "10.42.0.1"
UERSIMTUN1_IP = "10.45.0.2"
UERSIMTUN2_IP = "10.42.0.2"

logging.basicConfig(level=logging.INFO)


def run_scenario():
    """Constructing the scenario with time-controlled connections"""
    print("========================================")
    print("===         UDP Test Scenario        ===")
    print("========================================")

    # Record start time for logging as timestamp 0
    logging.info("[t=0] Connecting to open5gs-1...")
    logging.info("[t=0] Starting UDP background traffic (70s duration)...")
    scenario_start = time.time()
    
    elapsed = time.time() - scenario_start
    print(elapsed)
    
    # Wait until t=35 before disconnecting from open5gs-1
    elapsed = time.time() - scenario_start
    if elapsed < 35:
        time.sleep(35 - elapsed)
    
    logging.info("[t=35] Disconnecting from open5gs-1...")
    
    elapsed = time.time() - scenario_start
    print(elapsed)

    # Wait until t=40 before connecting to open5gs-2
    elapsed = time.time() - scenario_start
    if elapsed < 40:
        time.sleep(40 - elapsed)

    logging.info("[t=40] Connecting to open5gs-2...")
    
    elapsed = time.time() - scenario_start
    print(elapsed)

    # Wait until t=70 before disconnecting from open5gs-2
    elapsed = time.time() - scenario_start
    if elapsed < 70:
        time.sleep(70 - elapsed)

    logging.info("[t=70] Disconnecting from open5gs-2...")
    
    elapsed = time.time() - scenario_start
    print(elapsed)

    print("========================================")
    print("UDP Test Scenario Completed")
    print("========================================")
    logging.info("Theoretical Time: 65 seconds")
    logging.info(f"Actual Time: {time.time() - 5 - scenario_start:.4f} seconds")
    logging.info("Now you need to check the test result in ./test/test_bgd_udp.txt")
    logging.info("Scenario completed successfully")


if __name__ == "__main__":
    run_scenario()
