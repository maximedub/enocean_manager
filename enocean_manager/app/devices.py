import json
import os
from eep import parse_eep_file

# Chemin vers le fichier JSON de persistance
DEVICES_FILE = "/data/devices.json"

# Initialise le fichier s'il n'existe pas
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
    with open(DEVICES_FILE, "r") as f:
        raw_devices = json.load(f)

    enriched = []
    for d in raw_devices:
        eep_file = f"/app/eep/D2-{d['eep_code']}.xml"
        eep_info = parse_eep_file(eep_file) if os.path.exists(eep_file) else None
        enriched.append({
            "id": d.get("id"),
            "eep_code": d.get("eep_code"),
            "eep_file": eep_file if os.path.exists(eep_file) else None,
            "eep_info": eep_info
        })
    return enriched
