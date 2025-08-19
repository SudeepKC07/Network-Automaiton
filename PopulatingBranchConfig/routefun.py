# routefun.py
from vpnfun import ho_vpn_name, br_vpn_name

def horoute(ho_device, br_device):
    """
    Static route on HO pointing to Branch LAN via HO-BR-VPN interface.
    """
    return [
        "config router static",
        "edit 0",  # append a new static route
        f"set dst {br_device['LAN']} {br_device['subnet']}",
        f"set device {ho_vpn_name(ho_device['DEV'], br_device['DEV'])}",
        "next",
        "end",
    ]

def brroute(br_device, ho_device):
    """
    Static route on BR pointing to HO LAN via BR-HO-VPN interface.
    """
    return [
        "config router static",
        "edit 0",  # append a new static route
        f"set dst {ho_device['LAN']} {ho_device['subnet']}",
        f"set device {br_vpn_name(br_device['DEV'], ho_device['DEV'])}",
        "next",
        "end",
    ]
