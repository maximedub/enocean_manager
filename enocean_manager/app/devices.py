import os
import json
from eep import EEPDevice

PAIRED_DEVICES_FILE = os.getenv("PAIRED_DEVICES_FILE", "/data/devices.json")


# Initialisation du fichier si inexistant
if not os.path.exists(DEVICES_FILE):
    with open(DEVICES_FILE, "w") as f:
        json.dump([], f)


def load_devices():
    """Charge les périphériques appairés depuis le fichier"""
    try:
        with open(DEVICES_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def save_device(device):
    """Ajoute un nouveau périphérique s’il n’est pas déjà enregistré"""
    devices = load_devices()
    if device not in devices:
        devices.append(device)
        with open(DEVICES_FILE, "w") as f:
            json.dump(devices, f, indent=2)


def remove_device(device):
    """Supprime un périphérique de la base"""
    devices = load_devices()
    new_devices = [d for d in devices if d != device]
    with open(DEVICES_FILE, "w") as f:
        json.dump(new_devices, f, indent=2)

def get_devices():
    if not os.path.exists(PAIRED_DEVICES_FILE):
        return []
    with open(PAIRED_DEVICES_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

__all__ = [
    "save_device",
    "get_devices",
    "get_device",
    "EEPDevice"
]
