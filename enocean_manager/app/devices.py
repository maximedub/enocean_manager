# devices.py
import json, os
from eep import EEPRegistry

DEVICES_FILE = "/data/devices.json"

def _ensure_file():
    d = os.path.dirname(DEVICES_FILE)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    if not os.path.exists(DEVICES_FILE):
        with open(DEVICES_FILE, "w") as f:
            json.dump([], f)

def save_device(device):
    _ensure_file()
    with open(DEVICES_FILE, "r+", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []
        if device not in data:
            data.append(device)
            f.seek(0)
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.truncate()

def get_devices():
    if not os.path.exists(DEVICES_FILE):
        return []
    with open(DEVICES_FILE, "r", encoding="utf-8") as fh:
        raw_devices = json.load(fh)

    enriched = []
    reg = None
    try:
        reg = EEPRegistry(os.environ.get("EEP_JSON_DIR"))
    except Exception:
        pass

    for d in raw_devices:
        info = dict(d)
        code = d.get("eep_code") or d.get("eep")
        if code and reg:
            try:
                p = reg.load(code)
                info["eep_info"] = {
                    "code": p.code,
                    "rorg": p.rorg,
                    "func": p.func,
                    "type": p.type,
                    "description": p.description,
                }
            except Exception as e:
                info["eep_info"] = {"error": str(e)}
        enriched.append(info)
    return enriched
