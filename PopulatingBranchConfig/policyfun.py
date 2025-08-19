LAN_IF = "port2"

def _vpn_if(local_dev, peer_dev):
    """Generate VPN interface name (must match vpnfun naming)."""
    return f"{local_dev}-{peer_dev}-VPN"


def hopolicy(ho_device, br_device, start_id=1):
    """
    Generate firewall policies for HO side towards a Branch.
    Ensures exactly 2 policies with unique IDs.
    """
    local = ho_device["DEV"]
    peer = br_device["DEV"]
    vpnif = _vpn_if(local, peer)

    policies = [
        "config firewall policy",

        # LAN -> BR
        f"edit {start_id}",
        f"set name LAN-to-{peer}",
        f"set srcintf {LAN_IF}",
        f"set dstintf {vpnif}",
        "set srcaddr all",
        "set dstaddr all",
        "set action accept",
        "set schedule always",
        "set service ALL",
        "next",

        # BR -> LAN
        f"edit {start_id + 1}",
        f"set name {peer}-to-LAN",
        f"set srcintf {vpnif}",
        f"set dstintf {LAN_IF}",
        "set srcaddr all",
        "set dstaddr all",
        "set action accept",
        "set schedule always",
        "set service ALL",
        "next",

        "end"
    ]
    return policies


def brpolicy(br_device, ho_device, start_id=1):
    """
    Generate firewall policies for Branch side towards HO.
    Ensures exactly 2 policies with unique IDs.
    """
    local = br_device["DEV"]
    peer = ho_device["DEV"]
    vpnif = _vpn_if(local, peer)

    policies = [
        "config firewall policy",

        # LAN -> HO
        f"edit {start_id}",
        f"set name LAN-to-{peer}",
        f"set srcintf {LAN_IF}",
        f"set dstintf {vpnif}",
        "set srcaddr all",
        "set dstaddr all",
        "set action accept",
        "set schedule always",
        "set service ALL",
        "next",

        # HO -> LAN
        f"edit {start_id + 1}",
        f"set name {peer}-to-LAN",
        f"set srcintf {vpnif}",
        f"set dstintf {LAN_IF}",
        "set srcaddr all",
        "set dstaddr all",
        "set action accept",
        "set schedule always",
        "set service ALL",
        "next",

        "end"
    ]
    return policies
