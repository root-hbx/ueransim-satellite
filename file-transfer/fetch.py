import os
import subprocess
import threading
import time
import signal
from typing import Optional, Union
from network_sim import ensure_dir

def fetch_file(
    net_interface: str, 
    file_name: str, 
    cdn_url: str, 
    log_file_path: str="./file-x/logging_without_file_arg.txt",
    timeout: Optional[int] = None,
    return_thread: bool = True
) -> Union[threading.Thread, bool]:
    """
    Download a file from specified URL using a specific network interface
    and log curl's progress to a file.

    Args:
        net_interface: Network interface name
        file_name: Output file name
        cdn_url: URL to download the file from
        log_file_path: Path to log file
        timeout: Maximum time to wait in seconds (None for no timeout)
        return_thread: If True, return Thread object (async). If False, run synchronously and return bool.
    
    Returns:
        threading.Thread if return_thread=True (async mode)
        bool if return_thread=False (sync mode)
    """
    
    def _fetch_file_sync() -> bool:
        """Internal synchronous implementation"""
        start_time = None
        process = None
        ensure_dir(log_file_path)
        ori_file_size_bytes = 0 if not os.path.exists(file_name) else os.path.getsize(file_name)

        # Create references for signal handler
        process_ref = [None]
        start_time_ref = [None]
        download_interrupted_ref = [False]
        ori_file_size_bytes_ref = [ori_file_size_bytes]

        timeout_timer = None
        def timeout_handler():
            """SIGINT handler: simulates Ctrl+C to the curl process."""
            if process_ref[0] and process_ref[0].poll() is None:
                try:
                    # SIGINT to curl process (== Ctrl+C)
                    process_ref[0].send_signal(signal.SIGINT)
                    print(f"\nTimeout reached! "
                        f"Sent SIGINT to curl process (PID: {process_ref[0].pid})")
                    
                except ProcessLookupError:
                    print("Process already terminated")
                except Exception as e:
                    print(f"Error sending signal to process: {e}")
            
            download_interrupted_ref[0] = True
            print(f"Download timed out after {timeout} seconds!")

        def signal_handler(sig, frame):
            if process_ref[0] and process_ref[0].poll() is None:
                process_ref[0].terminate()  # terminate curl process
            download_interrupted_ref[0] = True
            print("\nDownload interrupted by user!")
            # no exit(1), since we wanna get statistics in the finally block
            return

        # 只在主线程中设置信号处理器
        original_handler = None
        setup_signal_handler = False
        try:
            original_handler = signal.getsignal(signal.SIGINT)
            signal.signal(signal.SIGINT, signal_handler)
            setup_signal_handler = True
        except ValueError:
            # 在子线程中运行，跳过信号处理器设置
            pass

        try:
            print(f"Starting download from {cdn_url} to {file_name}")
            print(f"Using network interface: {net_interface}")
            if timeout:
                print(f"Timeout set to {timeout} seconds")

            start_time = time.perf_counter()
            start_time_ref[0] = start_time
            
            if timeout:
                timeout_timer = threading.Timer(timeout, timeout_handler)
                timeout_timer.start()
            
            curl_cmd = [
                "curl",
                "--interface", net_interface,
                "-C", "-",  # Resume download if possible
                "-o", file_name,
                "-L", # Follow redirects
                "--no-progress-meter",
                cdn_url
            ]
            
            with open(log_file_path, 'a', encoding='utf-8') as log_file_handle:
                log_file_handle.write("\n=== NEW DOWNLOAD SESSION ===\n")
                log_file_handle.write(f"Command: {' '.join(curl_cmd)}\n")
                log_file_handle.write(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                if timeout:
                    log_file_handle.write(f"Timeout: {timeout} seconds\n")
                log_file_handle.write("\n")
            
            # Start the curl process
            process = subprocess.Popen(
                curl_cmd, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, 
                universal_newlines=True
            )
            process_ref[0] = process
            
            # Store process reference globally for external control
            global curl_process
            curl_process = process
            
            stdout, stderr = process.communicate()
            
            process_was_interrupted = False
            if process.returncode == -signal.SIGINT or process.returncode == -2:
                # 进程被SIGINT中断
                process_was_interrupted = True
                download_interrupted_ref[0] = True
            elif process.returncode < 0:
                # 进程被其他信号终止
                process_was_interrupted = True
                download_interrupted_ref[0] = True

            with open(log_file_path, 'a', encoding='utf-8') as log_file_handle:
                log_file_handle.write(f"Process return code: {process.returncode}\n")
                if stdout:
                    log_file_handle.write("=== STDOUT ===\n")
                    log_file_handle.write(stdout)
                    log_file_handle.write("\n")
                if stderr:
                    log_file_handle.write("=== STDERR ===\n")
                    log_file_handle.write(stderr)
                    log_file_handle.write("\n")

            if download_interrupted_ref[0] or process_was_interrupted:
                # Ctrl+C by "user manually" or "timeout reached"
                if os.path.exists(file_name) and start_time_ref[0] is not None:
                    end_time = time.perf_counter()
                    duration = end_time - start_time_ref[0]
                    try:
                        # Statistics for download with ctrl+c
                        cur_file_size_bytes = os.path.getsize(file_name)
                        downloaded_bytes = cur_file_size_bytes - ori_file_size_bytes_ref[0]
                        file_size_mb = downloaded_bytes / (1024 * 1024)
                        speed_mbps = (file_size_mb / duration) if duration > 0 else 0
                        
                        stats_info = f"""
Download interrupted by user!
Partial download statistics:
File name: {file_name}

Total size fetched: {cur_file_size_bytes / (1024 * 1024):.2f} MB
Size downloaded in this period: {file_size_mb:.2f} MB

Time elapsed: {duration:.2f} seconds
Average speed: {speed_mbps:.2f} MBps
"""
                        
                        with open(log_file_path, 'a', encoding='utf-8') as log_file_handle:
                            log_file_handle.write("\n=== DOWNLOAD INTERRUPTED ===\n")
                            log_file_handle.write(stats_info)
                            log_file_handle.write(f"Interrupted at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                            log_file_handle.write("\n\n")

                    except Exception as e:
                        error_msg = f"Error calculating statistics for partial download: {e}"
                        print(error_msg)
                        with open(log_file_path, 'a', encoding='utf-8') as log_file_handle:
                            log_file_handle.write(f"\n=== ERROR ===\n{error_msg}\n")
                return False

            # Working normally, check return code in case
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

            # Statistics for successful download
            end_time = time.perf_counter()
            duration = end_time - start_time

            cur_file_size_bytes = os.path.getsize(file_name)
            downloaded_bytes = cur_file_size_bytes - ori_file_size_bytes
            file_size_mb = downloaded_bytes / (1024 * 1024)  # MB
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
            if timeout_timer:
                timeout_timer.cancel()
            if setup_signal_handler and original_handler:
                signal.signal(signal.SIGINT, original_handler)

    # 根据参数决定返回线程还是直接执行
    if return_thread:
        # 异步模式：创建并启动线程
        thread = threading.Thread(
            target=_fetch_file_sync,
            name=f"fetch_file-{net_interface}-{os.path.basename(file_name)}"
        )
        thread.start()
        return thread
    else:
        # 同步模式：直接执行并返回结果
        return _fetch_file_sync()


# 全局变量用于存储当前的curl进程
curl_process = None