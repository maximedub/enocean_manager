# API FastAPI : expose CRUD + import/export des 2 YAML + UI statique
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .models import Device
from . import registry
from .yaml_manager import write_both_yaml_files, read_both_yaml_files

# Chemins injectés par run.sh (configurables dans l'add-on)
AUTO_OUTPUT_PATH = os.environ.get("AUTO_OUTPUT_PATH", "/config/packages/enocean_auto.yaml")
AUTO_BACKUP_PATH = os.environ.get("AUTO_BACKUP_PATH", "/config/packages/enocean_auto.backup.yaml")
CONFIG_OUTPUT_PATH = os.environ.get("CONFIG_OUTPUT_PATH", "/config/packages/enocean_yaml_config.yaml")
CONFIG_BACKUP_PATH = os.environ.get("CONFIG_BACKUP_PATH", "/config/packages/enocean_yaml_config.backup.yaml")

app = FastAPI(title="EnOcean YAML Manager", version="0.2.0")

# Sert l'UI web (HTML/JS/CSS)
app.mount("/ui", StaticFiles(directory="/app/web", html=True), name="ui")

@app.get("/")
def root_redirect():
    """Page racine → UI."""
    return FileResponse("/app/web/index.html")

# ------- Registry CRUD -------
@app.get("/api/devices")
def list_devices():
    """Liste complète des appareils (registre)."""
    return registry.list_devices().model_dump()

@app.post("/api/devices")
def add_or_update_device(device: Device):
    """Ajoute ou met à jour un appareil."""
    reg = registry.upsert_device(device)
    return reg.model_dump()

@app.get("/api/devices/{id_hex_or_key}")
def get_device(id_hex_or_key: str):
    """Récupère un appareil par ID (ou clé interne)."""
    dev = registry.get_device(id_hex_or_key)
    if not dev:
        raise HTTPException(status_code=404, detail="Not found")
    return dev.model_dump()

@app.delete("/api/devices/{id_hex_or_key}")
def delete_device(id_hex_or_key: str):
    """Supprime un appareil par ID (ou clé interne)."""
    reg = registry.delete_device(id_hex_or_key)
    return reg.model_dump()

# ------- Import/Export YAML -------
@app.post("/api/export")
def export_yaml():
    """
    Écrit les 2 YAML :
    - AUTO (pour HA)
    - CONFIG (groupements lisibles)
    """
    reg = registry.list_devices()
    auto_out, cfg_out = write_both_yaml_files(
        reg,
        AUTO_OUTPUT_PATH, AUTO_BACKUP_PATH,
        CONFIG_OUTPUT_PATH, CONFIG_BACKUP_PATH
    )
    return {"ok": True, "auto_output": auto_out, "config_output": cfg_out}

@app.post("/api/import")
def import_yaml():
    """
    Lit les 2 YAML existants puis remplit le registre interne (→ UI).
    """
    reg = read_both_yaml_files(AUTO_OUTPUT_PATH, CONFIG_OUTPUT_PATH)
    registry.save_registry(reg)
    return {"ok": True, "imported": len(reg.devices)}
