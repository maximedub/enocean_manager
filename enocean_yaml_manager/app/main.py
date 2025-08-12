# API FastAPI : endpoints YAML + EEP + UI (Ingress-friendly)
# ----------------------------------------------------------
# - Sert l'UI statique à la racine "/" (compatible Ingress)
# - Expose /api/health pour le watchdog Supervisor
# - Middleware "anti //": normalise le chemin des requêtes (remplace // par /)
# - Endpoints: /api/paths, /api/eep, /api/suggest/channels,
#              /api/devices*, /api/export, /api/import
import os
import re  # <- pour normaliser les chemins
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .models import Device
from . import registry
from .yaml_manager import write_both_yaml_files, read_both_yaml_files
from .eep_loader import list_eep, suggest_channels

# --- Variables d'environnement injectées par run.sh (ou options add-on) ---
AUTO_OUTPUT_PATH = os.environ.get("AUTO_OUTPUT_PATH", "/config/packages/enocean_auto.yaml")  # package HA
AUTO_BACKUP_PATH = os.environ.get("AUTO_BACKUP_PATH", "/config/enocean_manager/backups/enocean_auto.yaml.bak")
CONFIG_OUTPUT_PATH = os.environ.get("CONFIG_OUTPUT_PATH", "/config/enocean_yaml_config.yaml")  # hors /packages
CONFIG_BACKUP_PATH = os.environ.get("CONFIG_BACKUP_PATH", "/config/enocean_manager/backups/enocean_yaml_config.yaml.bak")

# --- App FastAPI ---
app = FastAPI(title="EnOcean YAML Manager", version="0.3.5")

# ----------------------------------------------------------
# Middleware: normalise les chemins (évite //api/... -> /api/...)
# ----------------------------------------------------------
@app.middleware("http")
async def normalize_double_slashes(request: Request, call_next):
  """
  Certains proxys / résolutions de liens peuvent produire des chemins
  avec plusieurs '/' consécutifs. FastAPI/Starlette ne route pas '//' sur
  '/'. On normalise donc le chemin avant le routage.
  """
  path = request.scope.get("path", "")
  norm = re.sub(r"/{2,}", "/", path) or "/"
  if norm != path:
    request.scope["path"] = norm  # on écrase le path au plus tôt
  response = await call_next(request)
  return response

# -----------------------
# Santé / Watchdog
# -----------------------
@app.get("/api/health")
def api_health():
  """Endpoint de santé très simple. Retourne ok=True si l'API est vivante."""
  return JSONResponse({"ok": True})

# -----------------------
# Infos chemins (affichage dans l’UI)
# -----------------------
@app.get("/api/paths")
def api_paths():
  """Retourne les chemins de fichiers effectivement utilisés par l'add-on."""
  return {
    "auto_output_path": AUTO_OUTPUT_PATH,
    "auto_backup_path": AUTO_BACKUP_PATH,
    "config_output_path": CONFIG_OUTPUT_PATH,
    "config_backup_path": CONFIG_BACKUP_PATH,
  }

# -----------------------
# EEP (liste + suggestion de canaux)
# -----------------------
@app.get("/api/eep")
def api_list_eep():
  """Liste des EEP disponibles (chargés depuis /app/eep/*.json)."""
  return {"profiles": list_eep()}

@app.get("/api/suggest/channels")
def api_suggest_channels(eep: str = Query(...)):
  """Renvoie la plage de canaux par défaut (si connue) pour l'EEP donné."""
  return {"eep": eep, "channels": suggest_channels(eep)}

# -----------------------
# Registry CRUD (appareils)
# -----------------------
@app.get("/api/devices")
def list_devices():
  """Retourne le registre complet (toutes les entités)."""
  return registry.list_devices().model_dump()

@app.post("/api/devices")
def add_or_update_device(device: Device):
  """Ajoute ou met à jour un appareil dans le registre."""
  reg = registry.upsert_device(device)
  return reg.model_dump()

@app.get("/api/devices/{id_hex_or_key}")
def get_device(id_hex_or_key: str):
  """Récupère un appareil par son ID (ou sa clé interne)."""
  dev = registry.get_device(id_hex_or_key)
  if not dev:
    raise HTTPException(status_code=404, detail="Not found")
  return dev.model_dump()

@app.delete("/api/devices/{id_hex_or_key}")
def delete_device(id_hex_or_key: str):
  """Supprime un appareil par son ID (ou clé interne)."""
  reg = registry.delete_device(id_hex_or_key)
  return reg.model_dump()

# -----------------------
# Import / Export YAML
# -----------------------
@app.post("/api/export")
def export_yaml():
  """Écrit les 2 YAML (auto + config) et leurs backups éventuels."""
  reg = registry.list_devices()
  auto_out, cfg_out = write_both_yaml_files(
    reg,
    AUTO_OUTPUT_PATH, AUTO_BACKUP_PATH,
    CONFIG_OUTPUT_PATH, CONFIG_BACKUP_PATH
  )
  return {"ok": True, "auto_output": auto_out, "config_output": cfg_out}

@app.post("/api/import")
def import_yaml():
  """Lit les 2 YAML (auto + config), fusionne et sauvegarde le registre."""
  reg = read_both_yaml_files(AUTO_OUTPUT_PATH, CONFIG_OUTPUT_PATH)
  registry.save_registry(reg)
  return {"ok": True, "imported": len(reg.devices)}

# -----------------------
# UI statique (Ingress)
# -----------------------
# IMPORTANT Ingress :
#  - l’UI doit être servie à la RACINE "/" (html=True) pour fonctionner
#    derrière /api/hassio_ingress/<token> avec des URLs relatives.
#  - aucun @app.get("/") supplémentaire pour éviter les collisions de routage.
app.mount("/", StaticFiles(directory="/app/web", html=True), name="ui_root")
