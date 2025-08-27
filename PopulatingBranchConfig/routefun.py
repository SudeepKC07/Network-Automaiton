# routefun.py

from vpnfun import ho_vpn_name, br_vpn_name

def _get_existing_routes(conn):
    """
    Parse 'show router static' into:
    {
      1: {"dst": "10.10.20.0 255.255.255.0", "device": "HO-BR1-VPN"},
      ...
    }
    """
    output = conn.send_command("show router static")
    routes = {}
    rid = None
    buf = {}

    for raw in output.splitlines():
        line = raw.strip()
        if line.startswith("edit "):
            try:
                rid = int(line.split()[1])
                buf = {}
            except:
                rid = None
        elif rid is not None and line.startswith("set "):
            parts = line.split(maxsplit=2)
            if len(parts) == 3:
                key, val = parts[1], parts[2].strip('"')
                buf[key] = val
        elif line == "next" and rid is not None:
            if buf:
                routes[rid] = buf
            rid, buf = None, {}
    return routes

def _next_free_id(routes_dict):
    rid = 1
    while rid in routes_dict:
        rid += 1
    return rid

def horoute(conn, ho_device, br_device):
    desired_dst = f"{br_device['LAN']} {br_device['subnet']}"
    desired_dev = ho_vpn_name(ho_device["DEV"], br_device["DEV"])

    routes = _get_existing_routes(conn)
    for rid, r in routes.items():
        if r.get("dst") == desired_dst and r.get("device") == desired_dev:
            print(f"✅ Static route exists (id {rid}): {desired_dst} via {desired_dev}; skipping.")
            return []

    new_id = _next_free_id(routes)
    return [
        "config router static",
        f"edit {new_id}",
        f"set dst {desired_dst}",
        f"set device {desired_dev}",
        "next",
        "end",
    ]

def brroute(conn, br_device, ho_device):
    desired_dst = f"{ho_device['LAN']} {ho_device['subnet']}"
    desired_dev = br_vpn_name(br_device["DEV"], ho_device["DEV"])

    routes = _get_existing_routes(conn)
    for rid, r in routes.items():
        if r.get("dst") == desired_dst and r.get("device") == desired_dev:
            print(f"✅ Static route exists (id {rid}): {desired_dst} via {desired_dev}; skipping.")
            return []

    new_id = _next_free_id(routes)
    return [
        "config router static",
        f"edit {new_id}",
        f"set dst {desired_dst}",
        f"set device {desired_dev}",
        "next",
        "end",
    ]
