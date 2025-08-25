# routefun.py
from vpnfun import ho_vpn_name, br_vpn_name

def horoute(ho_device, br_device):
    return [
        "config router static",
        "edit 0",
        f"set dst {br_device['LAN']} {br_device['subnet']}",
        f"set device {ho_vpn_name(ho_device['DEV'], br_device['DEV'])}",
        "next",
        "end",
    ]

def brroute(br_device, ho_device):
    return [
        "config router static",
        "edit 0",
        f"set dst {ho_device['LAN']} {ho_device['subnet']}",
        f"set device {br_vpn_name(br_device['DEV'], ho_device['DEV'])}",
        "next",
        "end",
    ]
