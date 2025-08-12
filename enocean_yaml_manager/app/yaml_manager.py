# -*- coding: utf-8 -*-
"""
Entrées/Sorties YAML pour EnOcean YAML Manager.

Ce module s'occupe :
- d'écrire *deux* fichiers YAML :
  1) `enocean_auto.yaml` : **package HA** consommé par l'intégration EnOcean
     (contient les plateformes HA "enocean": switch/light/sensor/binary_sensor)
  2) `enocean_yaml_config.yaml` : **fichier de configuration lisible**
     (regroupements récepteur/émetteur, EEP, options, etc.)
- de lire ces deux fichiers pour reconstruire un `Registry`.
- de sauvegarder un **backup** des fichiers, mais **hors `/packages/`**,
  pour éviter que Home Assistant ne tente de charger le backup comme un package.

Le contenu écrit pour `enocean_auto.yaml` respecte les schémas HA :
- binary_sensor.platform: enocean  (id: [int,int,int,int], name?, device_class?)
- switch.platform: enocean         (id: [....], channel: int, name?)
- light.platform: enocean          (sender_id: [....] requis, id: [....] optionnel, name?)
- sensor.platform: enocean         (id: [....], device_class?, min_temp?, max_temp?, range_from?, range_to?, name?)
Réf. code source HA : plateformes "enocean" binary_sensor / light / sensor.  # noqa
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple, Optional

import os
import yaml

from .models import (
    Registry,
    Device,
    ChannelConfig,   # alias -> Channel (cf. models.py)
    ChannelEmitter,
)

# -----------------------------------------------------------------------------
# Utilitaires
# -----------------------------------------------------------------------------

def _hex_id_to_octets(id_hex: Optional[str]) -> List[int]:
    """
    Convertit une chaîne hex 'FFAABBCC' en liste d'octets [255,170,187,204].
    - Retourne [] si id_hex est vide/None.
    - Tolère des espaces, met en MAJ, ignore '0x' si présent.
    """
    if not id_hex:
        return []
    s = id_hex.strip().upper().replace("0X", "")
    # On ne garde que les 8 premiers hex (4 octets EnOcean)
    s = s[:8]
    if len(s) != 8:
        # Défensif : si longueur inattendue, on complète / tronque.
        s = (s + ("0" * 8))[:8]
    return [int(s[i : i + 2], 16) for i in range(0, 8, 2)]


def _ensure_dir(p: Path) -> None:
    """Crée récursivement le dossier parent du chemin donné."""
    p.parent.mkdir(parents=True, exist_ok=True)


def _yaml_dump_to_file(path: Path, data: dict) -> None:
    """
    Écrit du YAML lisible :
    - sort_keys=False pour garder l’ordre logique,
    - allow_unicode=True pour conserver les accents,
    - default_flow_style=False pour listes/mappings multilignes.
    """
    _ensure_dir(path)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            data,
            f,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )


def _safe_backup(src_path: Path, backup_path: Path) -> None:
    """
    Sauvegarde le fichier `src_path` vers `backup_path` **hors /packages/**.
    - Si `backup_path` pointe dans /packages/, on le redirige vers :
      /config/enocean_manager/backups/<nom>.bak
    """
    if not src_path.exists():
        return

    effective_backup = backup_path
    try:
        # Si le backup est sous /packages/, on le déplace dans /config/enocean_manager/backups/
        if "/packages/" in str(backup_path):
            new_dir = Path("/config/enocean_manager/backups")
            new_dir.mkdir(parents=True, exist_ok=True)
            effective_backup = new_dir / (backup_path.name or f"{src_path.name}.bak")

        _ensure_dir(effective_backup)
        effective_backup.write_text(src_path.read_text(encoding="utf-8"), encoding="utf-8")
    except Exception:
        # En cas d'échec de backup, on n'empêche pas l'écriture principale.
        pass


def _auto_correct_config_target(path: Path) -> Path:
    """
    Si on tente d'écrire `enocean_yaml_config.yaml` dans /packages/,
    on corrige automatiquement vers /config/enocean_yaml_config.yaml.
    """
    if "/packages/" in str(path) and path.name.startswith("enocean_yaml_config"):
        return Path("/config/enocean_yaml_config.yaml")
    return path


# -----------------------------------------------------------------------------
# Génération des structures YAML HA (enocean_auto.yaml)
# -----------------------------------------------------------------------------

def _build_ha_entry_binary_sensor(emitter: ChannelEmitter) -> dict:
    """Construit une entrée HA pour un émetteur en tant que binary_sensor."""
    return {
        "platform": "enocean",
        "id": _hex_id_to_octets(emitter.id),
        **({"name": emitter.label} if emitter.label else {}),
    }


def _build_ha_entry_switch(device: Device, ch: ChannelConfig) -> dict:
    """Construit une entrée HA pour un canal de switch (récepteur)."""
    base_name = device.label or f"EnOcean {device.id_hex}"
    name = f"{base_name} - {ch.label}" if ch.label else base_name
    return {
        "platform": "enocean",
        "id": _hex_id_to_octets(device.id_hex),
        "channel": int(ch.channel),
        **({"name": name} if name else {}),
    }


def _build_ha_entry_light(device: Device) -> Optional[dict]:
    """Construit une entrée HA pour une light (reçoit + envoie via sender_id)."""
    if not device.light_sender or not device.light_sender.sender_id:
        # HA exige sender_id pour la light EnOcean → on ignore si absent
        return None
    entry = {
        "platform": "enocean",
        "sender_id": _hex_id_to_octets(device.light_sender.sender_id),
        **({"id": _hex_id_to_octets(device.id_hex)} if device.id_hex else {}),
        **({"name": device.label} if device.label else {}),
    }
    return entry


def _build_ha_entry_sensor(device: Device) -> dict:
    """Construit une entrée HA pour un capteur."""
    entry = {
        "platform": "enocean",
        "id": _hex_id_to_octets(device.id_hex),
        **({"name": device.label} if device.label else {}),
    }
    # Options supportées par le schéma HA (voir code core HA)
    if device.sensor_options:
        so = device.sensor_options
        if so.device_class:
            entry["device_class"] = so.device_class
        # Les suivantes sont optionnelles selon la classe
        if so.min_temp is not None:
            entry["min_temp"] = int(so.min_temp)
        if so.max_temp is not None:
            entry["max_temp"] = int(so.max_temp)
        if so.range_from is not None:
            entry["range_from"] = int(so.range_from)
        if so.range_to is not None:
            entry["range_to"] = int(so.range_to)
        # unit_of_measurement est ignorée ici (non prévue par le schéma HA)
    return entry


def _generate_auto_yaml_structure(reg: Registry) -> dict:
    """
    Construit la structure dict correspondant à `enocean_auto.yaml`.
    On n'inclut une section que si elle a au moins 1 entrée.
    """
    binary_sensors: List[dict] = []
    switches: List[dict] = []
    lights: List[dict] = []
    sensors: List[dict] = []

    # Pour éviter les doublons d’émetteurs transformés en binary_sensor
    seen_emitters: set[str] = set()

    for key, dev in (reg.devices or {}).items():
        if dev.ha_type == "switch":
            # Un switch HA est un récepteur avec au moins 1 canal
            for ch in (dev.channels or []):
                switches.append(_build_ha_entry_switch(dev, ch))
                # Si un émetteur (kind=binary_sensor) est attaché au canal, on peut l’exposer
                if ch.emitter and ch.emitter.id:
                    kind = (ch.emitter.kind or "binary_sensor").strip()
                    if kind == "binary_sensor":
                        eid = ch.emitter.id.upper().strip()
                        if eid not in seen_emitters:
                            binary_sensors.append(_build_ha_entry_binary_sensor(ch.emitter))
                            seen_emitters.add(eid)

        elif dev.ha_type == "light":
            # Light HA requiert sender_id – on ajoute l’entrée si complète
            entry = _build_ha_entry_light(dev)
            if entry:
                lights.append(entry)

        elif dev.ha_type == "sensor":
            sensors.append(_build_ha_entry_sensor(dev))

        # Les autres types ne sont pas gérés côté EnOcean (limités à ceux-ci)

    # Assemble le mapping top-level attendu par HA (packages)
    doc: dict = {}

    if binary_sensors:
        doc["binary_sensor"] = binary_sensors
    if switches:
        doc["switch"] = switches
    if lights:
        doc["light"] = lights
    if sensors:
        doc["sensor"] = sensors

    return doc


# -----------------------------------------------------------------------------
# Génération du YAML "config" (lisible, groupements)
# -----------------------------------------------------------------------------

def _generate_config_yaml_structure(reg: Registry) -> dict:
    """
    Construit une structure simple et lisible pour le fichier de config (hors HA).
    On exporte une liste de devices (pas un dict) pour éviter les collisions de clés.
    """
    devices_list: List[dict] = []
    for _key, dev in (reg.devices or {}).items():
        devices_list.append(dev.model_dump(exclude_none=True))
    return {"version": 1, "devices": devices_list}


# -----------------------------------------------------------------------------
# Fonctions publiques utilisées par l'API
# -----------------------------------------------------------------------------

def write_both_yaml_files(
    reg: Registry,
    auto_output_path: str,
    auto_backup_path: str,
    config_output_path: str,
    config_backup_path: str,
) -> Tuple[str, str]:
    """
    Écrit:
      - `auto_output_path` avec la configuration HA (packages)
      - `config_output_path` avec les groupements lisibles
    Crée une sauvegarde de chaque fichier juste avant l'écriture.

    Règles de sûreté:
    - **Backups hors /packages/** (redirigés si nécessaire).
    - **enocean_yaml_config.yaml** forcé hors /packages/.
    """
    # Normalise chemins
    auto_out = Path(auto_output_path)
    auto_bak = Path(auto_backup_path)
    cfg_out = _auto_correct_config_target(Path(config_output_path))
    cfg_bak = Path(config_backup_path)

    # Sauvegardes si les fichiers existent déjà
    _safe_backup(auto_out, auto_bak)
    _safe_backup(cfg_out, cfg_bak)

    # Génère la structure HA (packages) puis écrit
    auto_doc = _generate_auto_yaml_structure(reg)
    _yaml_dump_to_file(auto_out, auto_doc)

    # Génère la structure lisible de config puis écrit
    cfg_doc = _generate_config_yaml_structure(reg)
    _yaml_dump_to_file(cfg_out, cfg_doc)

    return (str(auto_out), str(cfg_out))


def read_both_yaml_files(auto_output_path: str, config_output_path: str) -> Registry:
    """
    Lit les 2 fichiers YAML si présents, et retourne un Registry reconstruit.

    Stratégie:
    - Si `config_output_path` existe : on le lit en priorité (source de vérité
      côté regroupements), et on reconstruit le `Registry`.
    - Sinon, on tente de lire `auto_output_path` (packages HA) et on infère
      un Registry minimal (utile pour un premier import).

    NB: La détection des émetteurs via `binary_sensor` est limitée (pas de lien
    automatique vers un canal précis, faute d’info dans HA) – on importe donc
    surtout les récepteurs (switch/light/sensor) depuis `auto.yaml`.
    """
    reg = Registry(devices={})

    cfg_path = Path(config_output_path)
    auto_path = Path(auto_output_path)

    if cfg_path.exists():
        try:
            raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
            for dev_obj in (raw.get("devices") or []):
                dev = Device.model_validate(dev_obj)
                # clé = id_hex (stable) ; si collision, on suffixe
                key = dev.id_hex or dev.label or f"device_{len(reg.devices)+1}"
                while key in reg.devices:
                    key = f"{key}#"
                reg.devices[key] = dev
            return reg
        except Exception:
            # si la lecture "config" échoue, on tente l'auto.yaml
            pass

    if auto_path.exists():
        try:
            raw = yaml.safe_load(auto_path.read_text(encoding="utf-8")) or {}
            # ---- switches ----
            for sw in (raw.get("switch") or []):
                if not isinstance(sw, dict) or sw.get("platform") != "enocean":
                    continue
                id_hex = "".join(f"{b:02X}" for b in (sw.get("id") or [])) or ""
                label = sw.get("name") or f"EnOcean {id_hex}"
                channel = int(sw.get("channel", 0))
                key = id_hex or f"switch_{len(reg.devices)+1}"
                dev = reg.devices.get(key)
                if not dev:
                    dev = Device(id_hex=id_hex, label=label, ha_type="switch", channels=[])
                    reg.devices[key] = dev
                # crée/ajoute le canal
                dev.channels.append(
                    ChannelConfig(channel=channel, label=f"Canal {channel}")
                )

            # ---- lights ----
            for lt in (raw.get("light") or []):
                if not isinstance(lt, dict) or lt.get("platform") != "enocean":
                    continue
                id_hex = "".join(f"{b:02X}" for b in (lt.get("id") or [])) or ""
                sender_hex = "".join(f"{b:02X}" for b in (lt.get("sender_id") or [])) or ""
                label = lt.get("name") or (f"Light {id_hex}" if id_hex else "Light (EnOcean)")
                key = id_hex or f"light_{len(reg.devices)+1}"
                dev = Device(
                    id_hex=id_hex,
                    label=label,
                    ha_type="light",
                    light_sender={"sender_id": sender_hex},  # validé par pydantic
                    channels=[],
                )
                reg.devices[key] = dev

            # ---- sensors ----
            for se in (raw.get("sensor") or []):
                if not isinstance(se, dict) or se.get("platform") != "enocean":
                    continue
                id_hex = "".join(f"{b:02X}" for b in (se.get("id") or [])) or ""
                label = se.get("name") or f"Sensor {id_hex}"
                key = id_hex or f"sensor_{len(reg.devices)+1}"
                so = {}
                # on récupère uniquement les champs supportés par le schéma HA
                for k in ("device_class", "min_temp", "max_temp", "range_from", "range_to"):
                    if k in se:
                        so[k] = se[k]
                dev = Device(
                    id_hex=id_hex,
                    label=label,
                    ha_type="sensor",
                    sensor_options=so or None,   # pydantic convertira en SensorOptions
                    channels=[],
                )
                reg.devices[key] = dev

        except Exception:
            # On retourne un registre vide si tout a échoué
            pass

    return reg
