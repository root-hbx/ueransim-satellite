import os
import subprocess
import time
import sys
import signal
from network_sim import ensure_dir

def _create_signal_handler(
    process_ref, 
    start_time_ref,
    file_name_ref,
    log_file_path_ref,
    download_interrupted_ref,
    ori_file_size_bytes_ref,
):
    """
    Create a signal handler for download interruption.
    
    Args:
        process_ref: Ref to the subprocess
        start_time_ref: Ref to start time
        file_name_ref: Ref to file name
        log_file_path_ref: Ref to log file path
        download_interrupted_ref: Ref to download interrupted flag
        ori_file_size_bytes_ref: Ref to original file size in bytes
    """
    def signal_handler(sig, frame):
        if process_ref[0] and process_ref[0].poll() is None:
            process_ref[0].terminate()  # terminate curl process

        download_interrupted_ref[0] = True
        print("\nDownload interrupted by user!")
        
        if os.path.exists(file_name_ref[0]) and start_time_ref[0] is not None:
            end_time = time.perf_counter()
            duration = end_time - start_time_ref[0]
            try:
                cur_file_size_bytes = os.path.getsize(file_name_ref[0])
                downloaded_bytes = cur_file_size_bytes - ori_file_size_bytes_ref[0]
                file_size_mb = downloaded_bytes / (1024 * 1024)
                speed_mbps = (file_size_mb / duration) if duration > 0 else 0
                
                stats_info = f"""
Download interrupted by user!
Partial download statistics:
File name: {file_name_ref[0]}

Total size fetched: {cur_file_size_bytes / (1024 * 1024):.2f} MB
Size downloaded in this period: {file_size_mb:.2f} MB

Time elapsed: {duration:.2f} seconds
Average speed: {speed_mbps:.2f} MBps
"""
                
                with open(log_file_path_ref[0], 'a', encoding='utf-8') as log_file_handle:
                    log_file_handle.write("\n=== DOWNLOAD INTERRUPTED ===\n")
                    log_file_handle.write(stats_info)
                    log_file_handle.write(f"Interrupted at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    log_file_handle.write("\n\n")

            except Exception as e:
                error_msg = f"Error calculating statistics for partial download: {e}"
                print(error_msg)
                with open(log_file_path_ref[0], 'a', encoding='utf-8') as log_file_handle:
                    log_file_handle.write(f"\n=== ERROR ===\n{error_msg}\n")

        sys.exit(1)

    return signal_handler


def fetch_file(
    net_interface, 
    file_name, 
    cdn_url, 
    log_file_path="./file-x/exp.txt"
):
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
    # download_interrupted = False
    ensure_dir(log_file_path)
    ori_file_size_bytes = 0 if not os.path.exists(file_name) else os.path.getsize(file_name)

    # Create references for signal handler
    process_ref = [None]
    start_time_ref = [None]
    file_name_ref = [file_name]
    log_file_path_ref = [log_file_path]
    download_interrupted_ref = [False]
    ori_file_size_bytes_ref = [ori_file_size_bytes]

    signal_handler = _create_signal_handler(
        process_ref, start_time_ref, file_name_ref, 
        log_file_path_ref, download_interrupted_ref,
        ori_file_size_bytes_ref
    )

    original_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        print(f"Starting download from {cdn_url} to {file_name}")
        print(f"Using network interface: {net_interface}")
        start_time = time.perf_counter()
        start_time_ref[0] = start_time
        
        curl_cmd = [
            "curl",
            "--interface", net_interface, #TODO(bxhu): linux works, macOS not
            "-C", "-",  # Resume download if possible
            "-o", file_name,
            "-L", # Follow redirects
            "--no-progress-meter",
            cdn_url
        ]
        
        with open(log_file_path, 'a', encoding='utf-8') as log_file_handle:
            log_file_handle.write(f"Command: {' '.join(curl_cmd)}\n")
            log_file_handle.write(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Start the curl process
        process = subprocess.Popen(
            curl_cmd, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, 
            universal_newlines=True
        )
        process_ref[0] = process
        
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

        if download_interrupted_ref[0]:
            return False

        if process.returncode != 0:
            error_msg = f"Download failed with error code {process.returncode}"
            with open(log_file_path, 'a', encoding='utf-8') as log_file_handle:
                log_file_handle.write("\n=== DOWNLOAD FAILED ===\n")
                log_file_handle.write(f"{error_msg}\n")
                log_file_handle.write(f"Failed at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

            return False

        if not os.path.exists(file_name):
            error_msg = f"Downloaded file {file_name} not found!"
            with open(log_file_path, 'a', encoding='utf-8') as log_file_handle:
                log_file_handle.write(f"\n=== FILE NOT FOUND ===\n{error_msg}\n")
            return False

        end_time = time.perf_counter()
        duration = end_time - start_time

        cur_file_size_bytes = os.path.getsize(file_name)
        downloaded_bytes = cur_file_size_bytes - ori_file_size_bytes
        file_size_mb = downloaded_bytes / (1024 * 1024)  # MB

        # Calculate download speed
        speed_mbps = (file_size_mb / duration) if duration > 0 else 0 # MBps

        success_info = f"""
Download completed successfully!
Final download statistics:
File name: {file_name}
File location: {os.path.abspath(file_name)}

Total size fetched: {cur_file_size_bytes / (1024 * 1024):.2f} MB
Size downloaded in this period: {file_size_mb:.2f} MB

Time elapsed: {duration:.2f} seconds
Average speed: {speed_mbps:.2f} MBps
"""

        with open(log_file_path, 'a', encoding='utf-8') as log_file_handle:
            log_file_handle.write("\n=== DOWNLOAD COMPLETED SUCCESSFULLY ===\n")
            log_file_handle.write(success_info)
            log_file_handle.write(f"Completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        return True

    except FileNotFoundError:
        error_msg = "Error: The 'curl' command was not found. " \
                   "Please ensure curl is installed and in your PATH."
        with open(log_file_path, 'a', encoding='utf-8') as log_file_handle:
            log_file_handle.write(f"\n=== CURL NOT FOUND ===\n{error_msg}\n")
        
        return False
    except Exception as e:
        error_msg = f"An unexpected error occurred: {e}"
        with open(log_file_path, 'a', encoding='utf-8') as log_file_handle:
            log_file_handle.write(f"\n=== UNEXPECTED ERROR ===\n{error_msg}\n")
            log_file_handle.write(f"Error occurred at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        return False
    finally:
        signal.signal(signal.SIGINT, original_handler)

# # Module Test
# if __name__ == "__main__":
#     net_if = "en0"
#     output_file = "./lecture12_SupML_buluc24.pdf"
#     test_url = "https://pub-cf250a7dff0b40dea71497e179a340b7.r2.dev/lecture12_SupML_buluc24.pdf"
#     result = fetch_file(net_if, output_file, test_url)
