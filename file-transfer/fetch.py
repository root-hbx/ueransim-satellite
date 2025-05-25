import os
import argparse
import subprocess
import time
import sys

def fetch_file(net_interface, file_name, cdn_url):
    """
    Download a file from specified URL using a specific network interface
    
    Parameters:
        net_interface: Network interface name
        file_name: Output file name
        cdn_url: URL to download the file from
    """
    try:
        print(f"Starting download from {cdn_url} to {file_name}")
        print(f"Using network interface: {net_interface}")
        
        start_time = time.perf_counter()
        
        # Construct curl command
        curl_cmd = [
            "curl",
            "--interface", net_interface,
            "-o", file_name,
            "-L", # Follow redirects
            "--progress-bar", # Show progress
            cdn_url
        ]
        
        # Execute curl command
        print("Executing curl command...")
        process = subprocess.Popen(curl_cmd, stdout=sys.stdout, stderr=subprocess.PIPE)
        
        # Wait for the process to complete
        _, stderr = process.communicate()
        
        # Check if the process completed successfully
        if process.returncode != 0:
            print(f"Download failed with error code {process.returncode}")
            print(f"Error message: {stderr.decode('utf-8')}")
            return False
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        # Get file size
        file_size_bytes = os.path.getsize(file_name)    # B
        file_size_mb = file_size_bytes / (1024 * 1024)  # MB
        
        # Calculate download speed
        speed_mbps = (file_size_mb / duration) if duration > 0 else 0 # MBps
        
        print(f"Download completed!")
        print("Statistics:")
        print(f"File size: {file_size_mb:.2f} MB")
        print(f"Time elapsed: {duration:.2f} seconds")
        print(f"Average speed: {speed_mbps:.2f} MBps")
        
        return True
            
    except Exception as e:
        print(f"Download failed: {e}")
        return False

def main():
    # Create command line argument parser
    parser = argparse.ArgumentParser(description='Download a file from CDN using specified network interface')
    parser.add_argument('--interface', '-i', dest='net_interface', required=True,
                        help='Network interface to use')
    parser.add_argument('--output', '-o', dest='file_name', required=True,
                        help='Output file name')
    parser.add_argument('--url', '-u', dest='cdn_url', required=True,
                        help='CDN file URL')
    
    # Parse command line arguments
    args = parser.parse_args()
    
    # Execute download
    fetch_file(args.net_interface, args.file_name, args.cdn_url)

if __name__ == "__main__":
    main()


