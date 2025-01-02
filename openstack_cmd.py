import paramiko
import getpass
import socket
from typing import Optional, List

def execute_ssh_command(
    host: str,
    username: str,
    password: Optional[str],
    key_path: Optional[str],
    commands: List[str]
) -> str:
    """
    Execute a list of commands on a remote server via SSH.

    :param host: The remote server hostname or IP address (str)
    :param username: The SSH username (str)
    :param password: The SSH password (Optional[str])
    :param key_path: The path to the SSH private key (Optional[str])
    :param commands: A list of commands to execute (List[str])
    :return: The output of the executed commands (str)
    """
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to the remote server
        if key_path:
            ssh_client.connect(host, username=username, key_filename=key_path, passphrase=password)
        else:
            ssh_client.connect(host, username=username, password=password)

        output = ""
        for command in commands:
            stdin, stdout, stderr = ssh_client.exec_command(command)
            stdout.channel.recv_exit_status()  # Wait for command to complete
            output += stdout.read().decode() + stderr.read().decode()

        return output
    except Exception as e:
        print(f"Error executing SSH command: {e}")
        return ""
    finally:
        ssh_client.close()

def collect_user_inputs() -> tuple:
    """Collect user inputs for SSH connection and command execution."""
    username = input("Enter LDAP username: ")
    password = getpass.getpass("Enter LDAP password: ")
    pod = input("Enter POD (e.g., POD01, POD02, MP02, MP03): ")
    dc = input("Enter DC (e.g., jed, sjc, phx, scl): ")
    command = input("Enter the command (e.g., openstack server list): ")
    return username, password, pod, dc, command

def map_values(pod: str, dc: str) -> tuple:
    """Map user inputs to corresponding values."""
    pod_mapping = {
        'POD01': 'pd01', 'POD02': 'pd02', 'POD03': 'pd03', 'POD04': 'pd04',
        'POD06': 'pd06', 'POD07': 'pd07', 'POD08': 'pd08', 'POD10': 'pd10',
        'POD11': 'pd11', 'POD17': 'pd17', 'POD19': 'pd19', 'POD20': 'pd20',
        'MP02': 'mp02', 'MP03': 'mp03'
    }
    dc_mapping = {
        'jed': 'pjed01', 'sjc': 'psjc01', 'phx': 'pphx01', 'scl': 'pscl01',
        'ams': 'pams01', 'lon': 'plon01', 'ruh': 'pruh01'
    }
    mapped_pod = pod_mapping.get(pod, pod)
    mapped_dc = dc_mapping.get(dc, dc)
    return mapped_pod, mapped_dc

def validate_hostname(host: str) -> None:
    """Validate if the hostname can be resolved."""
    try:
        socket.gethostbyname(host)
        print(f"Hostname {host} resolves correctly.")
    except socket.error as e:
        print(f"Hostname {host} does not resolve. Exiting.")
        raise Exception(f"Could not resolve hostname: {host}") from e

def execute_command(mapped_pod: str, mapped_dc: str, command: str, username: str, password: str) -> str:
    """Execute an OpenStack command on a remote host."""
    host = f"{mapped_dc}-vimmgmt.i.iotcc.cisco.com"
    print(f"Constructed Host: {host}")

    validate_hostname(host)

    openstack_command = [
        f"sudo -i -u root bash -c 'source openrc_{mapped_pod}-{mapped_dc} && {command}'"
    ]

    raw_output = execute_ssh_command(host, username, password, None, openstack_command)
    print("\nCommand Output:")
    print(raw_output)
    return raw_output

def main():
    while True:
        username, password, pod, dc, command = collect_user_inputs()
        mapped_pod, mapped_dc = map_values(pod, dc)
        execute_command(mapped_pod, mapped_dc, command, username, password)

        continue_prompt = input("Do you want to enter more commands (yes/no): ").strip().lower()
        if continue_prompt != 'yes':
            print("Exiting based on user input.")
            break

if __name__ == "__main__":
    main()
