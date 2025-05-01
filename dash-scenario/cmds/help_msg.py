import textwrap
import sys


def show_help():
    """Display detailed help information for all available commands"""
    help_text = """
    UERANSIM Satellite CLI Tool
    ==========================
    
    A command-line tool for managing UERANSIM satellite connections to different core networks.
    
    Available Commands:
    
    start <corenet>      Start connection to a core network
      Options:
        <corenet>        Core network to connect to (open5gs1 or open5gs2)
        -o, --output     Output file for logs (default: ./test/<corenet>_tcp_traffic.txt)
        -t, --gen-time   Traffic generation time in seconds (default: 30.0)
      
      Example:
        uersat start open5gs1 --gen-time 60
    
    switch <corenet>     Switch to a different core network
      Options:
        <corenet>        Core network to switch to (open5gs1 or open5gs2)
        -o, --output     Output file for logs (default: ./test/switch_to_<corenet>_tcp_traffic.txt)
        -t, --gen-time   Traffic generation time in seconds (default: 30.0)
      
      Example:
        uersat switch open5gs2 --output ./logs/switch.txt
    
    stop                 Stop current connection and clean up resources
      
      Example:
        uersat stop
    
    help                 Show this help message
    
    Usage Notes:
    - All commands requiring network changes need sudo/root privileges
    - Use 'start' to initiate a connection before using 'switch'
    - Each connection generates TCP traffic using iperf3
    - The tool maintains state between calls, so you can start, switch, or stop in separate sessions
    - Configuration files are expected in the config/ directory
    """
    
    # Print formatted help text
    print(textwrap.dedent(help_text).strip())
    
    # Return success code
    return 0


