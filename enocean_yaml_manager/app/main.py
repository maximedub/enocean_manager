# API FastAPI : CRUD + import/export + EEP + UI + Ingress + /api/paths
import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .models import Device
from . import registry
from .yaml_manager import write_both_yaml_files, read_both_yaml_files
from .eep_loader import list_eep, suggest_channels

AUTO_OUTPUT_PATH = os.environ.get("AUTO_OUTPUT_PATH", "/config/packages/enocean_auto.yaml")
AUTO_BACKUP_PATH = os.environ.get("AUTO_BACKUP_PATH", "/config/enocean_manager/backups/enocean_auto.yaml.bak")
CONFIG_OUTPUT_PATH = os.environ.get("CONFIG_OUTPUT_PATH", "/config/enocean_yaml_config.yaml")
CONFIG_BACKUP_PATH = os.environ.get("CONFIG_BACKUP_PATH", "/config/enocean_manager/backups/enocean_yaml_config.yaml.bak")

app = FastAPI(title="EnOcean YAML Manager", version="0.3.3")

# -----------------------
# Infos paths (UI)
# -----------------------
@app.get("/api/paths")
def api_paths():
    """Retourne les chemins actuellement utilisés par l'addon."""
    return {
        "auto_output_path": AUTO_OUTPUT_PATH,
        "auto_backup_path": AUTO_BACKUP_PATH,
        "config_output_path": CONFIG_OUTPUT_PATH,
        "config_backup_path": CONFIG_BACKUP_PATH,
    }

# -----------------------
# EEP
# -----------------------
@app.get("/api/eep")
def api_list_eep():
    return {"profiles": list_eep()}

@app.get("/api/suggest/channels")
def api_suggest_channels(eep: str = Query(...)):
    return {"eep": eep, "channels": suggest_channels(eep)}

# -----------------------
# Registry CRUD
# -----------------------
@app.get("/api/devices")
def list_devices():
    return registry.list_devices().model_dump()

@app.post("/api/devices")
def add_or_update_device(device: Device):
    reg = registry.upsert_device(device)
    return reg.model_dump()

@app.get("/api/devices/{id_hex_or_key}")
def get_device(id_hex_or_key: str):
    dev = registry.get_device(id_hex_or_key)
    if not dev:
        raise HTTPException(status_code=404, detail="Not found")
    return dev.model_dump()

@app.delete("/api/devices/{id_hex_or_key}")
def delete_device(id_hex_or_key: str):
    reg = registry.delete_device(id_hex_or_key)
    return reg.model_dump()

# -----------------------
# Import/Export YAML
# -----------------------
@app.post("/api/export")
def export_yaml():
    reg = registry.list_devices()
    auto_out, cfg_out = write_both_yaml_files(
        reg,
        AUTO_OUTPUT_PATH, AUTO_BACKUP_PATH,
        CONFIG_OUTPUT_PATH, CONFIG_BACKUP_PATH
    )
    return {"ok": True, "auto_output": auto_out, "config_output": cfg_out}

@app.post("/api/import")
def import_yaml():
    reg = read_both_yaml_files(AUTO_OUTPUT_PATH, CONFIG_OUTPUT_PATH)
    registry.save_registry(reg)
    return {"ok": True, "imported": len(reg.devices)}

# -----------------------
# UI statique (Ingress-friendly)
# -----------------------
app.mount("/", StaticFiles(directory="/app/web", html=True), name="ui_root")

@app.get("/")
def root_index():
    return FileResponse("/app/web/index.html")
