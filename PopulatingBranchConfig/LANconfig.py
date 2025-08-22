# LANconfig.py
def lanconfig(device):
    """
    Generate LAN (port2) configuration for a device.
    Uses Gateway (as IP) and Subnet from the CSV.
    """
    gw = device["Gateway"]
    subnet = device["subnet"]

    return [
        "config system interface",
        "edit port2",
        "set mode static",
        f"set ip {gw} {subnet}",
        "set allowaccess ping ssh https",
        "next",
        "end",
    ]
