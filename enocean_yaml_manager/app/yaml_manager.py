# Génération & lecture des 2 YAML :
#  - AUTO (consommé par HA) : binary_sensor / sensor / light / switch
#  - CONFIG (groupements lisibles) : mapping récepteurs ↔ émetteurs / canaux
import os
from typing import Dict, Any, List, Tuple
from ruamel.yaml import YAML
from .models import Registry, Device, ChannelConfig
from .utils import (
    hex_str_to_bytes_list,
    bytes_list_to_yaml_list,
    bytes_list_to_hex_str,
)

yaml = YAML()
yaml.default_flow_style = False

# ---------- Helpers conversions ----------
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
    sections clé : binary_sensor / light / sensor / switch.
    """
    tree: Dict[str, Any] = {}

    def add(platform: str, entry: Dict[str, Any]) -> None:
        if platform not in tree:
            tree[platform] = []
        tree[platform].append(entry)

    for dev in reg.devices.values():
        if dev.ha_type == "switch":
            # Un switch par canal
            for ch in (dev.channels or []):
                add("switch", {
                    "platform": "enocean",
                    "id": _enocean_id_list_maybe(dev.id_hex),
                    "name": ch.label or f"{dev.label} ch{ch.channel}",
                    "channel": int(ch.channel),
                })
        elif dev.ha_type == "light":
            # light : sender_id requis côté core HA
            if not dev.light_sender:
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
            # Paramètres température pour A5-10-xx si fournis
            if dev.sensor_options and dev.sensor_options.device_class == "temperature":
                entry.update({
                    "min_temp": dev.sensor_options.min_temp,
                    "max_temp": dev.sensor_options.max_temp,
                    "range_from": dev.sensor_options.range_from,
                    "range_to": dev.sensor_options.range_to,
                })
            add("sensor", entry)

    return tree

# ---------- Construction YAML CONFIG (groupements) ----------
def build_yaml_grouping_tree(reg: Registry) -> Dict[str, Any]:
    """
    Fichier lisible regroupant RX/TX :
    devices:
      - id: "0595DD72"
        label: "Lumière - Atelier"
        type: "switch"
        light_sender: "FFC6EA04"
        channels:
          - channel: 0
            label: "Atelier"
            emitters:
              - id: "051EF457"
                kind: "binary_sensor"
                label: "Inter gauche"
    """
    devices = []
    for dev in reg.devices.values():
        item: Dict[str, Any] = {
            "id": (dev.id_hex or ""),
            "label": dev.label,
            "type": dev.ha_type,
        }
        if dev.ha_type == "light" and dev.light_sender:
            item["light_sender"] = dev.light_sender.sender_id

        chs = []
        for ch in (dev.channels or []):
            ch_entry: Dict[str, Any] = {
                "channel": int(ch.channel),
                "label": ch.label or f"Canal {ch.channel}",
            }
            emitters = []
            if ch.emitter_id and ch.emitter_kind:
                emitters.append({
                    "id": ch.emitter_id,
                    "kind": ch.emitter_kind,
                    "label": ch.emitter_label or f"Émetteur canal {ch.channel}",
                })
            if emitters:
                ch_entry["emitters"] = emitters
            chs.append(ch_entry)
        if chs:
            item["channels"] = chs

        devices.append(item)

    return {"devices": devices}

# ---------- Écritures fichiers ----------
def _safe_backup(src_path: str, backup_path: str | None) -> None:
    """Sauvegarde du fichier existant (si présent). Échec silencieux."""
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
    # AUTO (consommé par HA)
    os.makedirs(os.path.dirname(auto_output_path), exist_ok=True)
    _safe_backup(auto_output_path, auto_backup_path)
    with open(auto_output_path, "w", encoding="utf-8") as f:
        yaml.dump(build_yaml_auto_tree(reg), f)

    # CONFIG (groupements lisibles)
    os.makedirs(os.path.dirname(config_output_path), exist_ok=True)
    _safe_backup(config_output_path, config_backup_path)
    with open(config_output_path, "w", encoding="utf-8") as f:
        yaml.dump(build_yaml_grouping_tree(reg), f)

    return auto_output_path, config_output_path

# ---------- Lectures fichiers → Registry ----------
def _load_yaml(path: str) -> Dict[str, Any]:
    """Charge un YAML en dict (ou dict vide si fichier absent)."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.load(f) or {}

def registry_from_auto_yaml(auto_tree: Dict[str, Any]) -> Registry:
    """Reconstruit un Registry minimal depuis le YAML AUTO."""
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
    """Injecte labels/émetteurs/canaux depuis le YAML CONFIG dans le Registry."""
    for item in (grouping_tree.get("devices") or []):
        dev_id_hex = (item.get("id") or "").upper()
        label = item.get("label") or "Appareil EnOcean"
        ha_type = item.get("type") or "switch"
        key = dev_id_hex or (f"LIGHT::{(label).upper()}" if ha_type == "light" else dev_id_hex)

        dev = reg.devices.get(key)
        if not dev:
            dev = Device(id_hex=dev_id_hex, label=label, ha_type=ha_type)
            reg.devices[key] = dev
        else:
            dev.label = label or dev.label

        if ha_type == "light" and (sender := item.get("light_sender")):
            dev.light_sender = {"sender_id": sender}

        channels = []
        for ch in (item.get("channels") or []):
            cc = ChannelConfig(
                channel=int(ch.get("channel", 0)),
                label=ch.get("label") or f"Canal {ch.get('channel', 0)}",
            )
            emitters = ch.get("emitters") or []
            if emitters:
                e0 = emitters[0]  # 1 émetteur max par canal
                cc.emitter_id = e0.get("id")
                cc.emitter_kind = e0.get("kind")
                cc.emitter_label = e0.get("label")
            channels.append(cc)
        if channels:
            dev.channels = channels

    return reg

def read_both_yaml_files(auto_path: str, config_path: str) -> Registry:
    """
    Lit auto.yaml + config.yaml et fusionne en un Registry.
    - auto.yaml → types/ids/paramètres côté HA
    - config.yaml → labels, light_sender, mapping émetteurs/canaux
    """
    auto_tree = _load_yaml(auto_path)
    config_tree = _load_yaml(config_path)
    reg = registry_from_auto_yaml(auto_tree)
    reg = merge_grouping_into_registry(reg, config_tree)
    return reg
