def lanconfig(device):
    """
    Generate LAN (port2) configuration for a device.
    Uses Gateway (as IP) and Subnet from the CSV.
    
    Example:
    config system interface
        edit port2
            set ip 10.10.10.1 255.255.255.0
            set allowaccess ping ssh https
            set mode static
        next
    end
    """

    gw = device["Gateway"]        # IP address for LAN interface
    subnet = device["subnet"]     # Subnet mask

    return [
        "config system interface",
        "edit port2",
        "set mode static",
        f"set ip {gw} {subnet}",
        "set allowaccess ping ssh https",
        "next",
        "end",
    ]
