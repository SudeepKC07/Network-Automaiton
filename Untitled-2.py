

from netmiko import ConnectHandler

# FortiGate device details
fortigate = {
    "device_type": "fortinet",
    "host": "192.168.209.217",  # FortiGate management IP
    "username": "admin",
    "password": "admin",
}

# Connect to the FortiGate
conn = ConnectHandler(**fortigate)

# Commands to set IP on port2
commands = [
    "config system interface",
    "edit port2",
    "set mode static",
    "set ip 192.168.10.1/24",  # Change to your required IP/mask
    "set allowaccess ping https ssh",  # Optional: enable mgmt protocols
    "next",
    "end"
]

# Send commands
output = conn.send_config_set(commands, exit_config_mode=False)
print(output)


# Disconnect
conn.disconnect()