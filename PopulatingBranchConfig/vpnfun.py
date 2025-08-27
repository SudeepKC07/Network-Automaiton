# vpnfun.py

def parse_vpn_phase1(conn):
    """Parse 'show vpn ipsec phase1-interface' into a dict."""
    output = conn.send_command("show vpn ipsec phase1-interface")
    vpns = {}
    current = None
    cfg = {}

    for line in output.splitlines():
        line = line.strip()
        if line.startswith("edit "):
            current = line.split()[1].strip('"')
            cfg = {}
        elif line.startswith("set ") and current:
            parts = line.split(maxsplit=2)
            if len(parts) == 3:
                key, val = parts[1], parts[2].strip('"')
                cfg[key] = val
        elif line == "next" and current:
            vpns[current] = cfg
            current, cfg = None, {}

    return vpns


def parse_vpn_phase2(conn):
    """Parse 'show vpn ipsec phase2-interface' into a dict."""
    output = conn.send_command("show vpn ipsec phase2-interface")
    vpns = {}
    current = None
    cfg = {}

    for line in output.splitlines():
        line = line.strip()
        if line.startswith("edit "):
            current = line.split()[1].strip('"')
            cfg = {}
        elif line.startswith("set ") and current:
            parts = line.split(maxsplit=2)
            if len(parts) == 3:
                key, val = parts[1], parts[2].strip('"')
                cfg[key] = val
        elif line == "next" and current:
            vpns[current] = cfg
            current, cfg = None, {}

    return vpns


def ho_vpn_name(ho_dev, br_dev):
    return f"{ho_dev}-{br_dev}-VPN"


def br_vpn_name(br_dev, ho_dev):
    return f"{br_dev}-{ho_dev}-VPN"


def build_phase1_cmds(name, desired, existing):
    cmds = [f"edit {name}"]
    for k, v in desired.items():
        if k == "psksecret":
            # Skip comparing PSK (always stored as ENC)
            if "psksecret" not in existing:
                cmds.append(f"set {k} {v}")
        else:
            if existing.get(k) != v:
                cmds.append(f"set {k} {v}")
    cmds.append("next")
    return cmds if len(cmds) > 2 else []


def build_phase2_cmds(name, desired, existing):
    cmds = [f"edit {name}"]
    for k, v in desired.items():
        if existing.get(k) != v:
            cmds.append(f"set {k} {v}")
    cmds.append("next")
    return cmds if len(cmds) > 2 else []


def hovpn(conn, ho, br):
    phase1_name = ho_vpn_name(ho["DEV"], br["DEV"])
    phase2_name = f"{phase1_name}-P2"

    desired_phase1 = {
        "interface": "port1",
        "ike-version": "2",
        "keylife": "28800",
        "peertype": "any",
        "net-device": "disable",
        "proposal": "des-sha256",
        "remote-gw": br["host"],
        "psksecret": "password",
    }

    desired_phase2 = {
        "phase1name": phase1_name,
        "proposal": "des-sha256",
        "dhgrp": "14",
        "keylifeseconds": "3600",
        "src-subnet": f"{ho['LAN']} {ho['subnet']}",
        "dst-subnet": f"{br['LAN']} {br['subnet']}",
    }

    existing_phase1 = parse_vpn_phase1(conn)
    existing_phase2 = parse_vpn_phase2(conn)

    cmds = []

    # Phase1
    if phase1_name in existing_phase1:
        phase1_cmds = build_phase1_cmds(phase1_name, desired_phase1, existing_phase1[phase1_name])
        if phase1_cmds:
            cmds += ["config vpn ipsec phase1-interface"] + phase1_cmds + ["end"]
        else:
            print(f"✅ Phase1 {phase1_name} already matches, skipping...")
    else:
        cmds += ["config vpn ipsec phase1-interface"] + build_phase1_cmds(phase1_name, desired_phase1, {}) + ["end"]

    # Phase2
    if phase2_name in existing_phase2:
        phase2_cmds = build_phase2_cmds(phase2_name, desired_phase2, existing_phase2[phase2_name])
        if phase2_cmds:
            cmds += ["config vpn ipsec phase2-interface"] + phase2_cmds + ["end"]
        else:
            print(f"✅ Phase2 {phase2_name} already matches, skipping...")
    else:
        cmds += ["config vpn ipsec phase2-interface"] + build_phase2_cmds(phase2_name, desired_phase2, {}) + ["end"]

    return cmds


def brvpn(conn, br, ho):
    phase1_name = br_vpn_name(br["DEV"], ho["DEV"])
    phase2_name = f"{phase1_name}-P2"

    desired_phase1 = {
        "interface": "port1",
        "ike-version": "2",
        "keylife": "28800",
        "peertype": "any",
        "net-device": "disable",
        "proposal": "des-sha256",
        "remote-gw": ho["host"],
        "psksecret": "password",
    }

    desired_phase2 = {
        "phase1name": phase1_name,
        "proposal": "des-sha256",
        "dhgrp": "14",
        "keylifeseconds": "3600",
        "src-subnet": f"{br['LAN']} {br['subnet']}",
        "dst-subnet": f"{ho['LAN']} {ho['subnet']}",
    }

    existing_phase1 = parse_vpn_phase1(conn)
    existing_phase2 = parse_vpn_phase2(conn)

    cmds = []

    # Phase1
    if phase1_name in existing_phase1:
        phase1_cmds = build_phase1_cmds(phase1_name, desired_phase1, existing_phase1[phase1_name])
        if phase1_cmds:
            cmds += ["config vpn ipsec phase1-interface"] + phase1_cmds + ["end"]
        else:
            print(f"✅ Phase1 {phase1_name} already matches, skipping...")
    else:
        cmds += ["config vpn ipsec phase1-interface"] + build_phase1_cmds(phase1_name, desired_phase1, {}) + ["end"]

    # Phase2
    if phase2_name in existing_phase2:
        phase2_cmds = build_phase2_cmds(phase2_name, desired_phase2, existing_phase2[phase2_name])
        if phase2_cmds:
            cmds += ["config vpn ipsec phase2-interface"] + phase2_cmds + ["end"]
        else:
            print(f"✅ Phase2 {phase2_name} already matches, skipping...")
    else:
        cmds += ["config vpn ipsec phase2-interface"] + build_phase2_cmds(phase2_name, desired_phase2, {}) + ["end"]

    return cmds
