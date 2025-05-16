import paramiko
import os
import sys
import getpass
import time
import tqdm


# prerequisites: "pip install paramiko tqdm"
def scp_download(service_name, service_ip, remote_path, local_path="."):
    """
    Fetch from a remote server using SCP
    
    Args:
        service_name: username for remote server
        service_ip: ip addr of remote server
        remote_path: remote file path to download
        local_path: local store path
    """
    local_file_path = None
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print(f"Currently connecting with {service_name}@{service_ip}...")
        
        password = getpass.getpass(f"Please input {service_name}"
                                   f"@{service_ip}'s password: ")
        ssh.connect(service_ip, username=service_name, password=password)

        sftp = ssh.open_sftp()

        # remote_path: "~/bxhu.txt"
        # remote_file_name: "bxhu.txt"
        remote_file_name = os.path.basename(remote_path)
        if local_path == ".":
            local_file_path = remote_file_name
        else:
            os.makedirs(local_path, exist_ok=True)
            local_file_path = os.path.join(local_path, remote_file_name)
        
        print(f"Downloading: {remote_path} -> {local_file_path}")

        file_size = sftp.stat(remote_path).st_size # B
        start_time = time.perf_counter()

        # Virtual progress bar using tqdm
        with tqdm.tqdm(total=file_size, unit='B', unit_scale=True, desc=remote_file_name) as pbar:
            def callback(bytes_transferred, total_bytes):
                pbar.update(bytes_transferred - pbar.n)
        
            sftp.get(remote_path, local_file_path, callback=callback)
        
        # End
        end_time = time.perf_counter()
        sftp.close()
        ssh.close()
        
        # Statistics
        download_time = end_time - start_time
        
        print(f"File Downloaded to: {local_file_path}")
        print(f"Download completed successfully.")
        print("=============================================")
        print(f"[Statistics]")
        print(f"File transfer time: {download_time:.2f} seconds")
        
        speed = file_size / download_time / 1024 / 1024  # MBps
        print(f"Average download speed: {speed:.2f} MBps")
        
        return True
    
    except Exception as e:
        print(f"Error: {str(e)}")
        if local_file_path and os.path.exists(local_file_path):
            try:
                if os.path.getsize(local_file_path) == 0:
                    os.remove(local_file_path)
                    print(f"Empty File Cleaned: {local_file_path}")
                else:
                    print(f"File {local_file_path} not empty, reserve it")
            except Exception as cleanup_error:
                print(f"Error when cleaning: {str(cleanup_error)}")

        return False


def main():
    service_name = "free5gc"
    service_ip = "172.16.162.135"
    remote_path = "/home/free5gc/QQ_3.2.15_250110_amd64_01.deb" # absolute path on remote server
    local_path = "./outputs"

    scp_download(service_name, service_ip, remote_path, local_path)

if __name__ == "__main__":
    main()