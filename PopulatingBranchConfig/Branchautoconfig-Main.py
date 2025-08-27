#latest cahnge date: 2025-08-27

import csv
import requests
from io import StringIO
from netmiko import ConnectHandler

from vpnfun import hovpn, brvpn
from policyfun import hopolicy, brpolicy
from routefun import horoute, brroute
from LANconfig import lanconfig

# CSV URL
csv_url = "https://raw.githubusercontent.com/SudeepKC07/DeviceLists/main/DeviceLists/fortigates.csv"

# Fetch & read CSV
resp = requests.get(csv_url)
resp.raise_for_status()
content = resp.text.lstrip("\ufeff")
reader = csv.DictReader(StringIO(content), delimiter=",")
devices = [{k.strip(): v.strip() for k, v in row.items()} for row in reader]

# Separate HO and BR
ho_devices = [d for d in devices if "HO" in d["DEV"]]
br_devices = [d for d in devices if "BR" in d["DEV"]]

print(f"HO devices: {[d['DEV'] for d in ho_devices]}")
print(f"BR devices: {[d['DEV'] for d in br_devices]}")

# ---------- HO Side ----------
for ho in ho_devices:
    print(f"\n🔹 Connecting to HO device {ho['DEV']} ({ho['host']})")
    try:
        conn = ConnectHandler(
            device_type="fortinet",
            host=ho["host"],
            username=ho["username"],
            password=ho["password"],
            port=int(ho["port"]),
        )
    except Exception as e:
        print(f"❌ Cannot connect to {ho['DEV']}: {e}")
        continue

    all_cfg = []
    all_cfg += lanconfig(conn, ho)

    for br in br_devices:
        all_cfg += hovpn(conn, ho, br)
        all_cfg += hopolicy(conn, ho, br)
        all_cfg += horoute(conn, ho, br)

    # Push config
    try:
        output = conn.send_config_set(all_cfg)
        print("\n===== CONFIGURATION CHANGES PUSHED =====")
        print(output)
    except Exception as e:
        print(f"❌ Error pushing config to {ho['DEV']}: {e}")

    # Show configuration
    for cmd in [
        "show system interface",
        "show vpn ipsec phase1-interface",
        "show vpn ipsec phase2-interface",
        "show router static",
        "show firewall policy",
    ]:
        print(f"\n>>> {cmd}")
        print(conn.send_command(cmd))

    conn.disconnect()

# ---------- BR Side ----------
for br in br_devices:
    print(f"\n🔹 Connecting to BR device {br['DEV']} ({br['host']})")
    try:
        conn = ConnectHandler(
            device_type="fortinet",
            host=br["host"],
            username=br["username"],
            password=br["password"],
            port=int(br["port"]),
        )
    except Exception as e:
        print(f"❌ Cannot connect to {br['DEV']}: {e}")
        continue

    all_cfg = []
    all_cfg += lanconfig(conn, br)

    for ho in ho_devices:
        all_cfg += brvpn(conn, br, ho)
        all_cfg += brpolicy(conn, br, ho)
        all_cfg += brroute(conn, br, ho)

    # Push config
    try:
        if all_cfg and any(cmd.strip() for cmd in all_cfg):
            print("\n===== CONFIGURATION CHANGES PUSHED =====")
            output = conn.send_config_set(all_cfg)
            print(output)
        else:
            print("\n===== CONFIGURATION CHANGES PUSHED =====")
            print("\n✅ No new configuration changes needed; skipping push.")
    except Exception as e:
        print(f"❌ Error pushing config to {br['DEV']}: {e}")

    # Show configuration
    for cmd in [
        "show system interface",
        "show vpn ipsec phase1-interface",
        "show vpn ipsec phase2-interface",
        "show router static",
        "show firewall policy",
    ]:
        print(f"\n>>> {cmd}")
        print(conn.send_command(cmd))

    conn.disconnect()
