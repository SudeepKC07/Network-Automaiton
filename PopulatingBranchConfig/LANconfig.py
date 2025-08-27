# LANconfig.py

LAN_IF = "port2"

def _normalize_allowaccess(value: str) -> str:
    """
    Normalize allowaccess tokens to a stable, sorted string
    so comparisons are order-agnostic.
    """
    if not value:
        return ""
    toks = [t for t in value.replace('"', "").split() if t]
    return " ".join(sorted(toks))

def _get_existing_interfaces(conn):
    """
    Parse 'show system interface' into:
    {
      "port2": {"mode": "static", "ip": "10.10.10.1 255.255.255.0", "allowaccess": "ping https ssh"},
      ...
    }
    """
    output = conn.send_command("show system interface")
    interfaces = {}
    cur = None
    buf = {}

    for raw in output.splitlines():
        line = raw.strip()
        if line.startswith("edit "):
            cur = line.split()[1].strip('"')
            buf = {}
        elif line.startswith("set ") and cur:
            parts = line.split(maxsplit=2)
            if len(parts) == 3:
                key, val = parts[1], parts[2].strip('"')
                buf[key] = val
        elif line == "next" and cur:
            # Default to static if mode not shown (FortiGate often omits static)
            if "mode" not in buf:
                buf["mode"] = "static"
            # Normalize allowaccess for comparison
            if "allowaccess" in buf:
                buf["allowaccess"] = _normalize_allowaccess(buf["allowaccess"])
            interfaces[cur] = buf
            cur, buf = None, {}

    return interfaces

def lanconfig(conn, device):
    """
    Build idempotent LAN configuration for port2.
    - If fully matches → return [] (skip)
    - If partial mismatch → push only the differing 'set' lines
    """
    gw = device["Gateway"]
    subnet = device["subnet"]

    desired = {
        "mode": "static",
        "ip": f"{gw} {subnet}",
        "allowaccess": _normalize_allowaccess("ping ssh https"),
    }

    existing = _get_existing_interfaces(conn)
    port = LAN_IF
    cur = existing.get(port, {"mode": "static"})  # default static if new

    # Normalize existing allowaccess for comparison (in case key missing)
    cur_allow = _normalize_allowaccess(cur.get("allowaccess", ""))
    cur_ip = cur.get("ip")
    cur_mode = cur.get("mode", "static")

    # Full match? skip
    if (cur_mode == desired["mode"]
        and cur_ip == desired["ip"]
        and cur_allow == desired["allowaccess"]):
        print(f"✅ {port} already matches; skipping.")
        return []

    # Otherwise push only what differs
    cmds = ["config system interface", f'edit {port}']
    if cur_mode != desired["mode"]:
        cmds.append(f"set mode {desired['mode']}")
    if cur_ip != desired["ip"]:
        cmds.append(f"set ip {desired['ip']}")
    if cur_allow != desired["allowaccess"]:
        # push in our normalized order
        cmds.append(f"set allowaccess {desired['allowaccess']}")
    cmds += ["next", "end"]
    return cmds
