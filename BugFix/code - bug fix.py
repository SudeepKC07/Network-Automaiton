###latest code

import csv
from netmiko import ConnectHandler
import traceback
import re
import requests
from io import StringIO

devices = []

# GitHub raw CSV URL
csv_url = "https://raw.githubusercontent.com/SudeepKC07/Network-Automaiton/device-loading/Fortigate Lists/fortigates.csv"

# Fetch CSV from GitHub
response = requests.get(csv_url)
response.raise_for_status()  # Raise error if request fails
csv_file = StringIO(response.text)

# Read devices from CSV
reader = csv.DictReader(csv_file)
for row in reader:
    devices.append(row)

print (f"{'DeviceIP:':<15} {'Interface Name:':<15} {'IP Address:':<15} {'Status:':<15}")

# Regex pattern to extract interface details from each line
interface_pattern = re.compile(
    r"name:\s*(\S+).*?"                      # capture interface name
    r"ip:\s*(\S+\s+\S+).*?"                  # capture IP address + mask (two parts)
    r"status:\s*(\S+)",                      # capture status (up/down)
    re.IGNORECASE
)

for device in devices:
    # Add device_type key manually
    device['device_type'] = 'fortinet'
    print(f"Connecting to {device['host']}...")
    interfaces_to_turn_up = []
    try:
        conn = ConnectHandler(**device)
        output = conn.send_command("get system interface")
        
        # Each interface block is a line starting with "== [ ... ]"
        # So split output by lines and check lines that start with "name:"
        # But in your output, each interface block is a single line, so split by lines and parse each line
        
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("name:"):
                match = interface_pattern.search(line)
                if match:
                    current_interface, current_ip, current_status = match.groups()
                    print(f"DEBUG: Interface={current_interface}, IP={current_ip}, Status={current_status}")
                    if current_ip == "0.0.0.0 0.0.0.0" and current_status.lower() == "down":
                        interfaces_to_turn_up.append(current_interface)
        
        if interfaces_to_turn_up:
            print(f"Interfaces to set UP on {device['host']}: {interfaces_to_turn_up}")
            for intf in interfaces_to_turn_up:
                commands = [
                    "config system interface",
                    f"edit {intf}",
                    "set status up",
                    "set description interface_turn_up_by_script",
                    "next",
                    "end"
                ]
                config_output = conn.send_config_set(commands, exit_config_mode=False)
                print(f"Set {intf} up:\n{config_output}")
        else:
            print(f"No interfaces require status change on {device['host']}.")
        print (f"{device['host']:<15} {', '.join(interfaces_to_turn_up) if interfaces_to_turn_up else '-':<15} {current_ip:<15} {current_status:<15}")
        conn.disconnect()
        print(f"Disconnected from {device['host']}.\n")

    except Exception as e:
        print(f"Error with device {device['host']}: {repr(e)}")
        traceback.print_exc()
