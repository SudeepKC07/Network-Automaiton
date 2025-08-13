import os

folder = r"C:\Users\sukcaaaa\OneDrive - TOLL GROUP\Fortigate Lists"
try:
    files = os.listdir(folder)
    print("Files in folder:")
    for f in files:
        print(f)
except Exception as e:
    print("Error listing folder:", e)
    