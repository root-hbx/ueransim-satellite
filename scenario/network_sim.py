import subprocess
import logging
import sys

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
                f"via {corenet_name if corenet_name else interface}...")

    ping_cmd = ["sudo", "ping", "-I", interface, "-c", str(count), target_ip]

    try:
        # `Popen` for real-time output
        # `Run` is not supportive for real-time output
        process = subprocess.Popen(
            ping_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # line-buffered
            universal_newlines=True
        )

        success = True
        stdout_lines = []

        # Real-time output for stdout
        print("============================================")
        print(f"=== PING {target_ip} via {corenet_name} ===")
        print("============================================")
        for line in process.stdout:
            line = line.strip()
            stdout_lines.append(line)
            print(f">> {line}")
            sys.stdout.flush()

        '''
        Return code = process.wait() should be the very first.
        Since `process.wait()` will block the process until it finishes,
        we can read the stdout and stderr after process ends (process safety).
        '''

        # Wait for the process to finish and get the return code
        return_code = process.wait()

        # Check for errors in stderr
        stderr = process.stderr.read()
        if stderr:
            print(f"ERROR: {stderr}")
            logging.error(f"Ping Error: {stderr}")
            success = False

        # Output -> Logging
        full_output = "\n".join(stdout_lines)

        # Check for process return code
        if return_code == 0:
            logging.info(f"Ping Test Successful - {corenet_name}")
            logging.info(full_output)
            print("====== PING Completed Successfully ======")
        else:
            logging.error(f"Ping Test Failed - {corenet_name}")
            logging.error(full_output)
            print("====== PING Failed ======")
            success = False

        return success
    except subprocess.TimeoutExpired:
        print(f"====== PING Timeout - {corenet_name} ======")
        logging.error(f"Ping Test Timeout - {corenet_name}")
        return False
    except KeyboardInterrupt:
        print("\n====== PING Interrupted by User ======")
        return False
    except Exception as e:
        print(f"====== PING Error: {str(e)} ======")
        logging.error(f"Ping Test Error: {str(e)}")
        return False
