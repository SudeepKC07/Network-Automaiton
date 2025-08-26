#latest cahnge date: 2025-08-22

import csv
import requests
from io import StringIO
from netmiko import ConnectHandler
import re

# ---------------- CSV / Device Loading ----------------
csv_url = "https://raw.githubusercontent.com/SudeepKC07/DeviceLists/main/DeviceLists/fortigates.csv"

resp = requests.get(csv_url)
resp.raise_for_status()
content = resp.text.lstrip("\ufeff")
reader = csv.DictReader(StringIO(content), delimiter=",")
devices = [{k.strip(): v.strip() for k, v in row.items()} for row in reader]

# Separate HO and BR devices
ho_devices = [d for d in devices if "HO" in d["DEV"]]
br_devices = [d for d in devices if "BR" in d["DEV"]]

# ---------------- Functions ----------------
def get_existing_vpns(conn):
    """Return a list of actual VPN names configured on the device."""
    output = conn.send_command("diagnose vpn tunnel list")
    vpns = set()
    for line in output.splitlines():
        match = re.search(r"name=([\w\-]+)", line)  # looks for "name=VPN-NAME"
        if match:
            vpns.add(match.group(1))
    return list(vpns)


def check_vpn_status(conn, vpn_name):
    """Check VPN status and return UP/DOWN and enc/dec packet counts."""
    output = conn.send_command("diagnose vpn tunnel list")

    status = "DOWN / Not Found"
    enc_pkts = 0
    dec_pkts = 0

    capture = False
    for line in output.splitlines():
        if f"name={vpn_name}" in line:
            capture = True
            match = re.search(r"status=(\w+)", line)
            if match:
                status = match.group(1).upper()

        if capture and "dec:pkts/bytes=" in line and "enc:pkts/bytes=" in line:
            dec_match = re.search(r"dec:pkts/bytes=(\d+)/\d+", line)
            enc_match = re.search(r"enc:pkts/bytes=(\d+)/\d+", line)
            if dec_match:
                dec_pkts = int(dec_match.group(1))
            if enc_match:
                enc_pkts = int(enc_match.group(1))
            break

    return status, enc_pkts, dec_pkts


vpn_status_summary = []


def test_device_vpns(device):
    print(f"\n🔹 Connecting to device {device['DEV']} ({device['host']})")
    try:
        conn = ConnectHandler(
            device_type="fortinet",
            host=device["host"],
            username=device["username"],
            password=device["password"],
            port=int(device["port"]),
            timeout=120
        )
    except Exception as e:
        print(f"❌ Cannot connect to {device['DEV']}: {e}")
        vpn_status_summary.append({
            "device": device["DEV"],
            "vpn": "NA",
            "status": "NA",
            "enc_packets": "NA",
            "dec_packets": "NA"
        })
        return

    existing_vpns = get_existing_vpns(conn)
    if not existing_vpns:
        print(f"ℹ️ No VPNs found on {device['DEV']}")
        vpn_status_summary.append({
            "device": device["DEV"],
            "vpn": "NA",
            "status": "NA",
            "enc_packets": "NA",
            "dec_packets": "NA"
        })
    else:
        for vpn_name in existing_vpns:
            print(f"Checking VPN: {vpn_name}")
            try:
                status, enc, dec = check_vpn_status(conn, vpn_name)
                vpn_status_summary.append({
                    "device": device["DEV"],
                    "vpn": vpn_name,
                    "status": status,
                    "enc_packets": enc,
                    "dec_packets": dec
                })
            except Exception as e:
                print(f"❌ VPN status check failed: {e}")
                vpn_status_summary.append({
                    "device": device["DEV"],
                    "vpn": vpn_name,
                    "status": "ERROR",
                    "enc_packets": "NA",
                    "dec_packets": "NA"
                })

    conn.disconnect()


# ---------------- Run Tests ----------------
for ho in ho_devices:
    test_device_vpns(ho)

for br in br_devices:
    test_device_vpns(br)

# ---------------- FINAL SUMMARY ----------------
print("\n\n===== VPN STATUS SUMMARY =====")
print(f"{'Device':<8} | {'VPN':<20} | {'Status':<12} | {'Enc pkts':<10} | {'Dec pkts':<10}")
print("-" * 70)
for item in vpn_status_summary:
    status_display = item['status']
    if status_display not in ["UP", "NA"]:
        status_display += " ⚠️"

    print(f"{item['device']:<8} | {item['vpn']:<20} | {status_display:<12} | {item['enc_packets']:<10} | {item['dec_packets']:<10}")
