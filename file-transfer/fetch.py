import os
import subprocess
import time
import sys
import signal
from network_sim import ensure_dir

def fetch_file(net_interface, file_name, cdn_url, log_file_path="./file-x/exp.txt"):
    """
    Download a file from specified URL using a specific network interface
    and log curl's progress to a file.

    Args:
        net_interface: Network interface name
        file_name: Output file name
        cdn_url: URL to download the file from
        log_file_path: Path to log file
    """
    start_time = None
    process = None
    download_interrupted = False
    ensure_dir(log_file_path)

    def signal_handler(sig, frame):
        nonlocal download_interrupted, process, start_time, file_name
        if process and process.poll() is None:
            process.terminate()  # terminate the curl process
        
        download_interrupted = True
        print("\nDownload interrupted by user!")
        
        if os.path.exists(file_name) and start_time is not None:
            end_time = time.perf_counter()
            duration = end_time - start_time
            try:
                file_size_bytes = os.path.getsize(file_name)
                file_size_mb = file_size_bytes / (1024 * 1024)
                speed_mbps = (file_size_mb / duration) if duration > 0 else 0
                
                # statistics
                stats_info = f"""
                Download interrupted by user!
                Partial download statistics:
                File name: {file_name}
                File size (partial): {file_size_mb:.2f} MB
                Time elapsed: {duration:.2f} seconds
                Average speed: {speed_mbps:.2f} MBps
                """
                print(stats_info)
                
                with open(log_file_path, 'a', encoding='utf-8') as log_file_handle:
                    log_file_handle.write("\n=== DOWNLOAD INTERRUPTED ===\n")
                    log_file_handle.write(stats_info)
                    log_file_handle.write(f"Interrupted at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    
            except Exception as e:
                error_msg = f"Error calculating statistics for partial download: {e}"
                print(error_msg)
                with open(log_file_path, 'a', encoding='utf-8') as log_file_handle:
                    log_file_handle.write(f"\n=== ERROR ===\n{error_msg}\n")
        
        sys.exit(1)

    original_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        print(f"Starting download from {cdn_url} to {file_name}")
        print(f"Using network interface: {net_interface}")
        start_time = time.perf_counter()
        
        # Construct curl command - 使用 --no-progress-meter 替代 --progress-bar 避免乱码
        curl_cmd = [
            "curl",
            # "--interface", net_interface,
            "-C", "-",  # Resume download if possible
            "-o", log_file_path,
            "-L", # Follow redirects
            "--no-progress-meter",
            cdn_url
        ]
        
        with open(log_file_path, 'w', encoding='utf-8') as log_file_handle:
            log_file_handle.write(f"Command: {' '.join(curl_cmd)}\n")
            log_file_handle.write(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        print("Executing curl command...")
        process = subprocess.Popen(
            curl_cmd, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, 
            universal_newlines=True
        )
        
        stdout, stderr = process.communicate()
        
        with open(log_file_path, 'a', encoding='utf-8') as log_file_handle:
            if stdout:
                log_file_handle.write("=== STDOUT ===\n")
                log_file_handle.write(stdout)
                log_file_handle.write("\n")
            if stderr:
                log_file_handle.write("=== STDERR ===\n")
                log_file_handle.write(stderr)
                log_file_handle.write("\n")

        # Check for interruption first
        if download_interrupted:
            # The signal handler already printed messages and exited,
            # but we return False to signify failure in the function's context.
            return False

        # Check if the process completed successfully
        if process.returncode != 0:
            error_msg = f"Download failed with error code {process.returncode}"
            print(error_msg)
            print(f"Error details have been logged to {log_file_path}")
            
            with open(log_file_path, 'a', encoding='utf-8') as log_file_handle:
                log_file_handle.write(f"\n=== DOWNLOAD FAILED ===\n")
                log_file_handle.write(f"{error_msg}\n")
                log_file_handle.write(f"Failed at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

            return False

        end_time = time.perf_counter()
        duration = end_time - start_time

        file_size_bytes = os.path.getsize(log_file_path)
        file_size_mb = file_size_bytes / (1024 * 1024)  # MB
        # Calculate download speed
        speed_mbps = (file_size_mb / duration) if duration > 0 else 0 # MBps

        # 打印详细信息包括文件位置
        success_info = f"""
            Download completed successfully!
            Final download statistics:
            File name: {file_name}
            File location: {log_file_path}
            File size: {file_size_mb:.2f} MB
            Time elapsed: {duration:.2f} seconds
            Average speed: {speed_mbps:.2f} MBps
            """
        print(success_info)

        with open(log_file_path, 'a', encoding='utf-8') as log_file_handle:
            log_file_handle.write("\n=== DOWNLOAD COMPLETED SUCCESSFULLY ===\n")
            log_file_handle.write(success_info)
            log_file_handle.write(f"Completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_file_handle.write(f"Curl output logged to: {os.path.abspath(log_file_path)}\n")

        return True

    except FileNotFoundError:
        error_msg = "Error: The 'curl' command was not found. Please ensure curl is installed and in your PATH."
        print(error_msg)
        
        with open(log_file_path, 'a', encoding='utf-8') as log_file_handle:
            log_file_handle.write(f"\n=== CURL NOT FOUND ===\n{error_msg}\n")
        return False
    except Exception as e:
        error_msg = f"An unexpected error occurred: {e}"
        print(error_msg)
        with open(log_file_path, 'a', encoding='utf-8') as log_file_handle:
            log_file_handle.write(f"\n=== UNEXPECTED ERROR ===\n{error_msg}\n")
            log_file_handle.write(f"Error occurred at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        return False
    finally:
        signal.signal(signal.SIGINT, original_handler)


if __name__ == "__main__":
    # Be sure that 'file-x' directory can be created or exists
    # For Linux, you might use 'eth0' or 'wlan0'. For macOS, 'en0'.
    # Use 'ip addr' or 'ifconfig' to find your network interface names.
    net_if = "en0" # Replace with your actual network interface
    output_file = "./lecture12_SupML_buluc24.pdf"
    # A test file URL (e.g., a 10MB test file)
    test_url = "https://pub-cf250a7dff0b40dea71497e179a340b7.r2.dev/lecture12_SupML_buluc24.pdf"
    result = fetch_file(net_if, output_file, test_url)
    
    if result:
        print(f"\nFile successfully downloaded to {os.path.abspath(output_file)}")
    else:
        print("\nDownload failed. Check log for details.")
