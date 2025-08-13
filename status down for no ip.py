import csv
from netmiko import ConnectHandler
import re

csv_file = "C:/Users/sukcaaaa/OneDrive - TOLL GROUP/Fortigate Lists/fortigates.csv"

def parse_interfaces(output):
    """
    Parses the output of 'get system interface' into a list of dicts per interface.
    """
    interfaces = []
    # Split by interface block using '== [ portX ]' or beginning for first interface
    blocks = re.split(r"== \[ [^\]]+ \]", output)
    
    # The first block is before the first '== [ portX ]', so contains first interface details
    # Clean empty blocks if any
    blocks = [blk.strip() for blk in blocks if blk.strip()]
    
    for block in blocks:
        # Extract key: value pairs by splitting on multiple spaces, careful with ip having two parts
        # We'll use regex to extract key: value pairs
        # Special: ip has 2 parts (IP and mask), so join them for 'ip'
        interface = {}
        # Match all key: value pairs (key: val val?)
        pattern = re.compile(r"(\w+): ([^\s]+(?: [^\s]+)?)")
        matches = pattern.findall(block)
        for k, v in matches:
            interface[k] = v
        interfaces.append(interface)
    return interfaces

def config_interface_status_change(conn, interface_name):
    """
    Sends configuration commands to set interface status to down.
    """
    commands = [
        "config system interface",
        f"edit {interface_name}",
        "set status down",
        f"set description interface_down_by_script"
        "next",
        "end"
    ]
    output = conn.send_config_set(commands, exit_config_mode=False)
    print(f"Changed status of {interface_name} to down:\n{output}")

with open(csv_file, mode='r') as file:
    csv_reader = csv.DictReader(file)
    for row in csv_reader:
        device = {
            'device_type': 'fortinet',
            'host': row['host'],
            'username': row['username'],
            'password': row['password'],
        }
        print(f"Connecting to {device['host']}...")
        try:
            conn = ConnectHandler(**device)
            output = conn.send_command("get system interface")
            
            interfaces = parse_interfaces(output)
            
            for intf in interfaces:
                ip = intf.get('ip', '')
                status = intf.get('status', '')
                name = intf.get('name', '')
                # Check for IP = '0.0.0.0 0.0.0.0' and status 'up'
                if ip == "0.0.0.0 0.0.0.0" and status.lower() == "up":
                    print(f"Interface {name} has IP {ip} and status {status}. Setting status to down.")
                    config_interface_status_change(conn, name)
                else:
                    print(f"Interface {name} is fine with IP {ip} and status {status}.")
            
            conn.disconnect()
            print(f"Disconnected from {device['host']}.\n")
        
        except Exception as e:
            print(f"Failed to connect or configure {device['host']}: {e}\n")
