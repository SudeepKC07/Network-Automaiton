# vpnfun.py

def ho_vpn_name(ho_dev, br_dev):
    """
    HO VPN name format: HO-BR1-VPN
    """
    return f"{ho_dev}-{br_dev}-VPN"

def br_vpn_name(br_dev, ho_dev):
    """
    BR VPN name format: BR1-HO-VPN
    """
    return f"{br_dev}-{ho_dev}-VPN"

def hovpn(ho, br):
    """
    Generate HO device VPN commands for a branch
    """
    phase1_name = ho_vpn_name(ho["DEV"], br["DEV"])
    phase2_name = f"{phase1_name}-P2"

    phase1_cfg = [
        f"edit {phase1_name}",
        "set interface port1",
        "set ike-version 2",
        "set keylife 28800",
        "set peertype any",
        "set net-device disable",
        "set proposal des-sha256",
        f"set remote-gw {br['host']}",
        "set psksecret password",
        "next"
    ]

    phase2_cfg = [
        f"edit {phase2_name}",
        f"set phase1name {phase1_name}",
        "set proposal des-sha256",
        "set dhgrp 14",
        "set keylifeseconds 3600",
        f"set src-subnet {ho['LAN']} {ho['subnet']}",
        f"set dst-subnet {br['LAN']} {br['subnet']}",
        "next"
    ]

    return ["config vpn ipsec phase1-interface"] + phase1_cfg + ["end"] + \
           ["config vpn ipsec phase2-interface"] + phase2_cfg + ["end"]

def brvpn(br, ho):
    """
    Generate Branch device VPN commands for HO
    """
    phase1_name = br_vpn_name(br["DEV"], ho["DEV"])
    phase2_name = f"{phase1_name}-P2"

    phase1_cfg = [
        f"edit {phase1_name}",
        "set interface port1",
        "set ike-version 2",
        "set keylife 28800",
        "set peertype any",
        "set net-device disable",
        "set proposal des-sha256",
        f"set remote-gw {ho['host']}",
        "set psksecret password",
        "next"
    ]

    phase2_cfg = [
        f"edit {phase2_name}",
        f"set phase1name {phase1_name}",
        "set proposal des-sha256",
        "set dhgrp 14",
        "set keylifeseconds 3600",
        f"set src-subnet {br['LAN']} {br['subnet']}",
        f"set dst-subnet {ho['LAN']} {ho['subnet']}",
        "next"
    ]

    return ["config vpn ipsec phase1-interface"] + phase1_cfg + ["end"] + \
           ["config vpn ipsec phase2-interface"] + phase2_cfg + ["end"]
