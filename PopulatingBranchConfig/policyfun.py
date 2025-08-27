LAN_IF = "port2"

def _vpn_if(local_dev, peer_dev):
    return f"{local_dev}-{peer_dev}-VPN"

def get_next_policy_id(existing_ids):
    next_id = 1
    while next_id in existing_ids:
        next_id += 1
    return next_id

def get_existing_policies(conn):
    """
    Fetch existing firewall policies and return:
    - List of existing policy IDs
    - Dictionary of existing policies with key attributes for duplicate checking
    """
    output = conn.send_command("show firewall policy")
    policies = {}
    current_id = None
    temp_policy = {}
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("edit "):
            current_id = int(line.split()[1])
            temp_policy = {}
        elif current_id is not None:
            if line.startswith("set srcintf "):
                temp_policy["srcintf"] = line.split()[2].strip('"')
            elif line.startswith("set dstintf "):
                temp_policy["dstintf"] = line.split()[2].strip('"')
            elif line.startswith("set srcaddr "):
                temp_policy["srcaddr"] = line.split()[2].strip('"')
            elif line.startswith("set dstaddr "):
                temp_policy["dstaddr"] = line.split()[2].strip('"')
            elif line.startswith("set service "):
                temp_policy["service"] = line.split()[2].strip('"')
            elif line.startswith("next") or line.startswith("end"):
                if current_id is not None and temp_policy:
                    policies[current_id] = temp_policy
                current_id = None
                temp_policy = {}
    return list(policies.keys()), policies

def hopolicy(conn, ho_device, br_device):
    local = ho_device["DEV"]
    peer = br_device["DEV"]
    vpnif = _vpn_if(local, peer)

    existing_ids, policies = get_existing_policies(conn)
    all_cfg = []
    policy_cfgs = [] #store only new policy lines

    # Define two policies
    policy_defs = [
        {
            "srcintf": LAN_IF,
            "dstintf": vpnif,
            "srcaddr": "all",
            "dstaddr": "all",
            "service": "ALL",
            "action": "accept",
            "schedule": "always",
            "name": f"LAN-to-{peer}"
        },
        {
            "srcintf": vpnif,
            "dstintf": LAN_IF,
            "srcaddr": "all",
            "dstaddr": "all",
            "service": "ALL",
            "action": "accept",
            "schedule": "always",
            "name": f"{peer}-to-LAN"
        }
    ]

    for policy in policy_defs:
        # Check duplicates
        duplicate = False
        for existing in policies.values():
            if all(
                existing.get(k) == policy[k]
                for k in ["srcintf", "dstintf", "srcaddr", "dstaddr", "service"]
            ):
                duplicate = True
                break
        if duplicate:
            print(f"✅ Policy {policy['name']} already exists; skipping...")
        else:
            policy_id = get_next_policy_id(existing_ids)
            existing_ids.append(policy_id)
            policy_cfgs += [
                f"edit {policy_id}",
                f"set name {policy['name']}",
                f"set srcintf {policy['srcintf']}",
                f"set dstintf {policy['dstintf']}",
                f"set srcaddr {policy['srcaddr']}",
                f"set dstaddr {policy['dstaddr']}",
                f"set action {policy['action']}",
                f"set schedule {policy['schedule']}",
                f"set service {policy['service']}",
                "next"
            ]
    if policy_cfgs:
        return ["config firewall policy"] + policy_cfgs + ["end"]
    else:
        return [] 

def brpolicy(conn, br_device, ho_device):
    # Same logic, swap roles
    return hopolicy(conn, br_device, ho_device)
