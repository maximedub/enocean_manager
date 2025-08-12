# Génération & lecture des 2 YAML :
#  - AUTO (consommé par HA) : binary_sensor / sensor / light / switch
#  - CONFIG (groupements lisibles) : mapping RX↔TX / canaux / EEP
import os
from typing import Dict, Any, List, Tuple
from ruamel.yaml import YAML
from .models import Registry, Device, ChannelConfig, ChannelEmitter
from .utils import (
    hex_str_to_bytes_list,
    bytes_list_to_yaml_list,
    bytes_list_to_hex_str,
)

yaml = YAML()
yaml.default_flow_style = False

def _enocean_id_list_maybe(id_hex: str) -> List[int]:
    """ID hex → liste d'int (vide si ID manquant/autorisé)."""
    if not id_hex:
        return []
    return bytes_list_to_yaml_list(hex_str_to_bytes_list(id_hex))

def _hex_from_yaml_id_list(lst: List[int]) -> str:
    """Liste d'int → hexa uppercase."""
    return bytes_list_to_hex_str([int(x) for x in (lst or [])])

# ---------- Construction YAML AUTO (pour HA) ----------
def build_yaml_auto_tree(reg: Registry) -> Dict[str, Any]:
    """
    Arbre YAML consommé par HA :
    sections : binary_sensor / light / sensor / switch.
    Chaque entrée inclut 'platform: enocean' + champs requis (id/sender_id/channel...).
    """
    tree: Dict[str, Any] = {}

    def add(platform: str, entry: Dict[str, Any]) -> None:
        if platform not in tree:
            tree[platform] = []
        tree[platform].append(entry)

    for dev in reg.devices.values():
        if dev.ha_type == "switch":
            for ch in (dev.channels or []):
                add("switch", {
                    "platform": "enocean",
                    "id": _enocean_id_list_maybe(dev.id_hex),
                    "name": ch.label or f"{dev.label} ch{ch.channel}",
                    "channel": int(ch.channel),
                })
            # Note : les émetteurs sont des entités séparées (binary_sensor/switch) —
            # ils ne sont pas imbriqués dans la plateforme switch du core.
            for ch in (dev.channels or []):
                if ch.emitter:
                    if ch.emitter.kind == "binary_sensor":
                        add("binary_sensor", {
                            "platform": "enocean",
                            "id": _enocean_id_list_maybe(ch.emitter.id),
                            "name": ch.emitter.label or f"{dev.label} canal {ch.channel} (émetteur)",
                        })
                    elif ch.emitter.kind == "switch":
                        add("switch", {
                            "platform": "enocean",
                            "id": _enocean_id_list_maybe(ch.emitter.id),
                            "name": ch.emitter.label or f"{dev.label} canal {ch.channel} (émetteur)",
                            # pas de channel ici : c'est un autre dispositif
                        })
        elif dev.ha_type == "light":
            if not dev.light_sender:
                # light sans sender_id : ignoré (exigé par le core)
                continue
            add("light", {
                "platform": "enocean",
                "id": _enocean_id_list_maybe(dev.id_hex),
                "sender_id": _enocean_id_list_maybe(dev.light_sender.sender_id),
                "name": dev.label,
            })
        elif dev.ha_type == "binary_sensor":
            add("binary_sensor", {
                "platform": "enocean",
                "id": _enocean_id_list_maybe(dev.id_hex),
                "name": dev.label,
            })
        elif dev.ha_type == "sensor":
            entry = {
                "platform": "enocean",
                "id": _enocean_id_list_maybe(dev.id_hex),
                "name": dev.label,
                "device_class": (dev.sensor_options.device_class
                                 if dev.sensor_options else "powersensor"),
            }
            if dev.sensor_options and dev.sensor_options.device_class == "temperature":
                entry.update({
                    "min_temp": dev.sensor_options.min_temp,
                    "max_temp": dev.sensor_options.max_temp,
                    "range_from": dev.sensor_options.range_from,
                    "range_to": dev.sensor_options.range_to,
                })
            add("sensor", entry)

    return tree

# ---------- Construction YAML CONFIG (groupements lisibles) ----------
def build_yaml_grouping_tree(reg: Registry) -> Dict[str, Any]:
    """
    devices[] :
      id, eep, type, label, light_sender?, channels[] {channel,label, emitter?{id,kind,label}}
    """
    devices = []
    for dev in reg.devices.values():
        item: Dict[str, Any] = {
            "id": (dev.id_hex or ""),
            "eep": dev.eep or None,
            "type": dev.ha_type,
            "label": dev.label,
        }
        if dev.ha_type == "light" and dev.light_sender:
            item["light_sender"] = dev.light_sender.sender_id

        if dev.ha_type == "switch" and dev.channels:
            chs = []
            for ch in dev.channels:
                ch_entry: Dict[str, Any] = {
                    "channel": int(ch.channel),
                    "label": ch.label or f"Canal {ch.channel}",
                }
                if ch.emitter:
                    ch_entry["emitter"] = {
                        "id": ch.emitter.id,
                        "kind": ch.emitter.kind,
                        "label": ch.emitter.label,
                    }
                chs.append(ch_entry)
            item["channels"] = chs

        devices.append(item)

    return {"version": 1, "devices": devices}

# ---------- Écritures fichiers ----------
def _safe_backup(src_path: str, backup_path: str | None) -> None:
    if not backup_path:
        return
    try:
        if os.path.exists(src_path):
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            with open(src_path, "r", encoding="utf-8") as src, \
                 open(backup_path, "w", encoding="utf-8") as dst:
                dst.write(src.read())
    except Exception:
        pass

def write_both_yaml_files(
    reg: Registry,
    auto_output_path: str,
    auto_backup_path: str | None,
    config_output_path: str,
    config_backup_path: str | None,
) -> Tuple[str, str]:
    """Écrit les 2 YAML (auto + config) + backups éventuels."""
    os.makedirs(os.path.dirname(auto_output_path), exist_ok=True)
    _safe_backup(auto_output_path, auto_backup_path)
    with open(auto_output_path, "w", encoding="utf-8") as f:
        yaml.dump(build_yaml_auto_tree(reg), f)

    os.makedirs(os.path.dirname(config_output_path), exist_ok=True)
    _safe_backup(config_output_path, config_backup_path)
    with open(config_output_path, "w", encoding="utf-8") as f:
        yaml.dump(build_yaml_grouping_tree(reg), f)

    return auto_output_path, config_output_path

# ---------- Lectures fichiers → Registry ----------
def _load_yaml(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.load(f) or {}

def registry_from_auto_yaml(auto_tree: Dict[str, Any]) -> Registry:
    """Reconstruit un Registry minimal depuis le YAML AUTO (types/ids/canaux)."""
    reg = Registry()

    # SWITCH
    for ent in auto_tree.get("switch", []) or []:
        if ent.get("platform") != "enocean":
            continue
        dev_id_hex = _hex_from_yaml_id_list(ent.get("id") or [])
        ch = int(ent.get("channel", 0))
        name = ent.get("name") or f"EnOcean Switch {ch}"
        key = dev_id_hex or ""
        dev = reg.devices.get(key) or Device(id_hex=dev_id_hex, label=name, ha_type="switch", channels=[])
        # Ajoute/merge canal
        dev.channels.append(ChannelConfig(channel=ch, label=name))
        reg.devices[key] = dev

    # LIGHT
    for ent in auto_tree.get("light", []) or []:
        if ent.get("platform") != "enocean":
            continue
        dev_id_hex = _hex_from_yaml_id_list(ent.get("id") or [])
        sender_hex = _hex_from_yaml_id_list(ent.get("sender_id") or [])
        name = ent.get("name") or "EnOcean Light"
        key = dev_id_hex or f"LIGHT::{name.upper()}"
        dev = Device(
            id_hex=dev_id_hex,
            label=name,
            ha_type="light",
            light_sender=None if not sender_hex else {"sender_id": sender_hex},
        )
        reg.devices[key] = dev

    # BINARY SENSOR
    for ent in auto_tree.get("binary_sensor", []) or []:
        if ent.get("platform") != "enocean":
            continue
        dev_id_hex = _hex_from_yaml_id_list(ent.get("id") or [])
        name = ent.get("name") or "EnOcean binary sensor"
        reg.devices[dev_id_hex] = Device(id_hex=dev_id_hex, label=name, ha_type="binary_sensor")

    # SENSOR
    for ent in auto_tree.get("sensor", []) or []:
        if ent.get("platform") != "enocean":
            continue
        dev_id_hex = _hex_from_yaml_id_list(ent.get("id") or [])
        name = ent.get("name") or "EnOcean sensor"
        device_class = ent.get("device_class") or "powersensor"
        dev = Device(
            id_hex=dev_id_hex,
            label=name,
            ha_type="sensor",
            sensor_options={
                "device_class": device_class,
                "min_temp": int(ent.get("min_temp", 0)),
                "max_temp": int(ent.get("max_temp", 40)),
                "range_from": int(ent.get("range_from", 255)),
                "range_to": int(ent.get("range_to", 0)),
            },
        )
        reg.devices[dev_id_hex] = dev

    return reg

def merge_grouping_into_registry(reg: Registry, grouping_tree: Dict[str, Any]) -> Registry:
    """Injecte labels/EEP/émetteurs/canaux depuis le YAML CONFIG dans le Registry."""
    devices = (grouping_tree.get("devices") or [])
    for item in devices:
        dev_id_hex = (item.get("id") or "").upper()
        label = item.get("label") or "Appareil EnOcean"
        ha_type = item.get("type") or "switch"
        eep = item.get("eep")
        key = dev_id_hex or (f"LIGHT::{(label).upper()}" if ha_type == "light" else dev_id_hex)

        dev = reg.devices.get(key)
        if not dev:
            dev = Device(id_hex=dev_id_hex, label=label, ha_type=ha_type, eep=eep)
            reg.devices[key] = dev
        else:
            dev.label = label or dev.label
            dev.eep = eep or dev.eep

        if ha_type == "light" and (sender := item.get("light_sender")):
            dev.light_sender = {"sender_id": sender}

        if ha_type == "switch":
            channels = []
            for ch in (item.get("channels") or []):
                emitter = None
                e = ch.get("emitter")
                if e and e.get("id") and e.get("kind"):
                    emitter = ChannelEmitter(id=e["id"], kind=e["kind"], label=e.get("label"))
                channels.append(ChannelConfig(
                    channel=int(ch.get("channel", 0)),
                    label=ch.get("label") or f"Canal {ch.get('channel', 0)}",
                    emitter=emitter
                ))
            if channels:
                dev.channels = channels

    return reg

def read_both_yaml_files(auto_path: str, config_path: str) -> Registry:
    """Lit auto.yaml + config.yaml et fusionne en un Registry."""
    auto_tree = _load_yaml(auto_path)
    config_tree = _load_yaml(config_path)
    reg = registry_from_auto_yaml(auto_tree)
    reg = merge_grouping_into_registry(reg, config_tree)
    return reg
