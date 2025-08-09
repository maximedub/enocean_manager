# app/devices.py
import json, os
from enocean_manager.eep_parser import parse_eep_file

DEVICES_FILE = "/data/devices.json"
if not os.path.exists(DEVICES_FILE):
    with open(DEVICES_FILE, "w") as f:
        json.dump([], f)

def save_device(device):
    with open(DEVICES_FILE, "r+") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []
        if device not in data:
            data.append(device)
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

def get_devices():
    if not os.path.exists(DEVICES_FILE):
        return []
    raw_devices = json.load(open(DEVICES_FILE))
    enriched = []
    for d in raw_devices:
        code = d.get("eep_code") or d.get("eep")
        info = parse_eep_file(code) if code else None
        enriched.append({**d, "eep_info": info})
    return enriched
