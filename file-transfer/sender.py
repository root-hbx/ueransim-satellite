import paramiko
import os
import sys
import getpass

# prerequisites: "pip install paramiko"
def scp_download(service_name, service_ip, remote_path, local_path="."):
    """
    Fetch from a remote server using SCP
    
    Args:
        service_name: username for remote server
        service_ip: ip addr of remote server
        remote_path: remote file path to download
        local_path: local store path
    """
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

        # Downloading...
        sftp.get(remote_path, local_file_path)
        
        # End
        sftp.close()
        ssh.close()
        
        print(f"File Downloaded to: {local_file_path}")
        print("Download completed successfully.")
        return True
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    service_name = "free5gc"
    service_ip = "172.16.162.135"
    remote_path = "~/bxhu.txt"
    local_path = "./outputs"

    scp_download(service_name, service_ip, remote_path, local_path)

if __name__ == "__main__":
    main()
