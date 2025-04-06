import subprocess
import logging

def perform_ping_test(
    target_ip: str,
    interface: str = "uersimtun0",
    count: int = 5,
    corenet_name: str = ""
) -> bool:
    """
    ping -I uersimtun0 172.16.162.135 via open5gsX

    Args:
        target_ip: target IP address (free5gc VM, for test)
        interface: net interface, default uersimtun0
        count: ping pkt num
        corenet_name: corenet name, for logging
    
    Returns:
        bool: True if ping is successful, False otherwise
    """
    
    logging.info(f"Ping Test: Transmitting {count} packets to {target_ip} "
                "via {corenet_name if corenet_name else interface}...")

    ping_cmd = ["sudo", "ping", "-I", interface, "-c", str(count), target_ip]
    
    try:
        result = subprocess.run(
            ping_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logging.info(f"Ping Test is Successful - {corenet_name}")
            logging.info(result.stdout)
            return True
        else:
            logging.error(f"Ping Test Failed - {corenet_name}")
            logging.error(f"Error: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logging.error(f"Ping Test Timeout - {corenet_name}")
        return False
    except Exception as e:
        logging.error(f"Ping Test Error: {str(e)}")
        return False

