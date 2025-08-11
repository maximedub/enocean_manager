# Persistance du registre (JSON sous /data) + CRUD
import os
from .models import Registry, Device

REG_PATH = "/data/enocean_registry.json"  # fichier persistant interne à l'add-on

def load_registry() -> Registry:
    """Charge le registre depuis /data, ou retourne un registre vide."""
    if not os.path.exists(REG_PATH):
        return Registry()
    with open(REG_PATH, "r", encoding="utf-8") as f:
        return Registry.model_validate_json(f.read())

def save_registry(reg: Registry) -> None:
    """Sauvegarde le registre dans /data (joli format)."""
    with open(REG_PATH, "w", encoding="utf-8") as f:
        f.write(reg.model_dump_json(indent=2))

def upsert_device(dev: Device) -> Registry:
    """
    Ajoute / met à jour un appareil (clé = ID normalisé).
    - Cas particulier des lights sans dev_id : on indexe par une clé spéciale.
    """
    key = (dev.id_hex or "").upper()
    if key == "":
        key = f"LIGHT::{(dev.label or '').upper()}"
    reg = load_registry()
    reg.devices[key] = dev
    save_registry(reg)
    return reg

def delete_device(id_hex_or_key: str) -> Registry:
    """Supprime un appareil par ID (ou par clé interne pour lights sans dev_id)."""
    reg = load_registry()
    reg.devices.pop((id_hex_or_key or "").upper(), None)
    save_registry(reg)
    return reg

def get_device(id_hex_or_key: str):
    """Récupère un appareil par son ID (ou clé interne)."""
    reg = load_registry()
    return reg.devices.get((id_hex_or_key or "").upper())

def list_devices() -> Registry:
    """Retourne tout le registre."""
    return load_registry()
