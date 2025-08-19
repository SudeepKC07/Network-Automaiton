import csv
import requests
from io import StringIO
from netmiko import ConnectHandler
import re
import time

from vpnfun import hovpn, brvpn
from policyfun import hopolicy, brpolicy
from routefun import horoute, brroute
from LANconfig import lanconfig

# CSV URL
csv_url = "https://raw.githubusercontent.com/SudeepKC07/Network-Automaiton/device-loading/Fortigate%20Lists/fortigates.csv"

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

# Store VPN summary
vpn_status_summary = []

# ---------- VPN STATUS FUNCTION ----------
def check_vpn_status(conn, vpn_name):
    """
    Parse VPN dec/enc counters directly from 'diagnose vpn tunnel list'.
    """
    try:
        output = conn.send_command_timing("diagnose vpn tunnel list", delay_factor=2)
        match = re.search(r"dec:pkts/bytes=(\d+)/(\d+),\s*enc:pkts/bytes=(\d+)/(\d+)", output)
        if match:
            dec_pkts = int(match.group(1))
            dec_bytes = int(match.group(2))
            enc_pkts = int(match.group(3))
            enc_bytes = int(match.group(4))
            status = "UP" if dec_pkts > 0 or enc_pkts > 0 else "DOWN"
            return status, enc_pkts, dec_pkts
        else:
            return "DOWN / Not Found", 0, 0
    except Exception as e:
        print(f"❌ Error checking VPN {vpn_name}: {e}")
        return "DOWN / Not Found", 0, 0

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
    all_cfg += lanconfig(ho)
    vpn_pairs = []

    for br in br_devices:
        vpn_name = f"{ho['DEV']}-{br['DEV']}-VPN"
        vpn_pairs.append((vpn_name, ho["Gateway"], br["Gateway"]))
        all_cfg += hovpn(ho, br)
        all_cfg += hopolicy(ho, br)
        all_cfg += horoute(ho, br)

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

    # Check VPN status
    for vpn_name, _, _ in vpn_pairs:
        status, enc, dec = check_vpn_status(conn, vpn_name)
        vpn_status_summary.append(
            {
                "device": ho["DEV"],
                "vpn": vpn_name,
                "status": status,
                "enc_packets": enc,
                "dec_packets": dec,
            }
        )

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
    all_cfg += lanconfig(br)
    vpn_pairs = []

    for ho in ho_devices:
        vpn_name = f"{br['DEV']}-{ho['DEV']}-VPN"
        vpn_pairs.append((vpn_name, br["Gateway"], ho["Gateway"]))
        all_cfg += brvpn(br, ho)
        all_cfg += brpolicy(br, ho)
        all_cfg += brroute(br, ho)

    # Push config
    try:
        output = conn.send_config_set(all_cfg)
        print("\n===== CONFIGURATION CHANGES PUSHED =====")
        print(output)
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

    # Check VPN status
    for vpn_name, _, _ in vpn_pairs:
        status, enc, dec = check_vpn_status(conn, vpn_name)
        vpn_status_summary.append(
            {
                "device": br["DEV"],
                "vpn": vpn_name,
                "status": status,
                "enc_packets": enc,
                "dec_packets": dec,
            }
        )

    conn.disconnect()

# ---------- FINAL VPN STATUS SUMMARY ----------
print("\n\n===== FINAL VPN STATUS SUMMARY =====")
for item in vpn_status_summary:
    print(
        f"Device: {item['device']} | VPN: {item['vpn']} | Status: {item['status']} | "
        f"Encrypted pkts: {item['enc_packets']} | Decrypted pkts: {item['dec_packets']}"
    )
