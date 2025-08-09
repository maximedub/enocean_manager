import os
import json
import logging
from typing import Optional

from flask import Flask, request, jsonify

from enocean_esp3 import (
    read_base_id, str_id_to_bytes, listen_teach_in, teachin_ute
)
from eep_loader import load_eep
from yaml_writer import add_switch_dual

OPTIONS_PATH = "/data/options.json"

# ----- Chargement options -----
def load_options():
    defaults = {
        "serial_port": "/dev/ttyUSB0",
        "eep_dir": "/app/eep_json",
        "log_level": "INFO",
        "listen_timeout": 12,
        "manufacturer_id": 65535,
        "write_yaml": True,
        "reload_on_write": False
    }
    try:
        with open(OPTIONS_PATH, "r") as f:
            data = json.load(f)
            defaults.update(data)
    except Exception:
        pass
    return defaults

opts = load_options()
logging.basicConfig(level=getattr(logging, opts.get("log_level", "INFO")))
log = logging.getLogger("enocean_ute_addon")

app = Flask(__name__)

# ----- Endpoints -----

@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.post("/pair/start")
def pair_start():
    """
    Mode AUTO: écoute. Si rien, option de forcer (UTE).
    Body JSON (optionnel):
    {
      "mode": "auto" | "force",
      "eep": "D2-01-12",     # si force sans découverte
      "channel": 0,          # si force
      "name_prefix": "Lumière - XXX"
    }
    """
    body = request.get_json(silent=True) or {}
    mode = body.get("mode", "auto").lower()
    eep  = body.get("eep")
    channel = int(body.get("channel", 0))
    name_prefix = body.get("name_prefix", "Actionneur EnOcean")

    serial_port = opts["serial_port"]
    eep_dir     = opts["eep_dir"]
    timeout     = int(opts["listen_timeout"])
    manuf_id    = int(opts["manufacturer_id"])
    write_yaml  = bool(opts["write_yaml"])

    # 1) Base ID de la clé
    try:
        base_id = read_base_id(serial_port)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Base ID non lisible: {e}"}), 400

    base_id_str = ":".join(f"{x:02X}" for x in base_id)
    log.info(f"Base ID clé: {base_id_str}")

    # 2) Mode AUTO: on écoute
    if mode == "auto":
        info = listen_teach_in(serial_port, timeout=timeout)
        if info:
            dev_id = info["id"]
            rorg   = info["rorg"]
            log.info(f"Découvert device RORG=0x{rorg:02X}, ID={dev_id}")

            # Hypothèse : si RORG D2 → actionneur 2 sorties. On écrit YAML directement.
            if write_yaml and rorg == 0xD2:
                add_switch_dual(dev_id, name_prefix)
                return jsonify({
                    "ok": True,
                    "mode": "auto",
                    "device_id": dev_id,
                    "rorg": f"0x{rorg:02X}",
                    "yaml_written": True,
                    "hint": "Rechargez la configuration Home Assistant (ou redémarrez) et testez ON/OFF."
                }), 200

            return jsonify({
                "ok": True,
                "mode": "auto",
                "device_id": dev_id,
                "rorg": f"0x{rorg:02X}",
                "yaml_written": False
            }), 200

        # sinon on tombera en force si eep est fourni
        if not eep:
            return jsonify({
                "ok": False,
                "error": "Aucune trame détectée en écoute. Fournissez 'eep' et 'channel' et relancez en mode 'force', ou rapprochez l’appareil et réessayez."
            }), 408
        mode = "force"  # bascule

    # 3) Mode FORCE: envoi UTE
    try:
        rorg, func, typ = load_eep(eep_dir, eep)
    except Exception as e:
        return jsonify({"ok": False, "error": f"EEP {eep} introuvable/illisible: {e}"}), 400

    # On exige le device cible (ID) depuis la requête en mode force (sinon on écoute d’abord).
    target = body.get("target_id")
    if not target:
        return jsonify({"ok": False, "error": "En mode 'force', fournissez 'target_id' (ex: 05:97:9C:FA)."}), 400

    try:
        target_id = str_id_to_bytes(target)
    except Exception as e:
        return jsonify({"ok": False, "error": f"target_id invalide: {e}"}), 400

    try:
        teachin_ute(
            serial_port=serial_port,
            sender_base_id=base_id,
            target_id=target_id,
            eep_rorg=rorg, eep_func=func, eep_type=typ,
            manufacturer_id=manuf_id,
            channel=channel
        )
    except Exception as e:
        return jsonify({"ok": False, "error": f"Échec envoi UTE: {e}"}), 500

    if write_yaml:
        add_switch_dual(target, name_prefix)

    return jsonify({
        "ok": True,
        "mode": "force",
        "eep": eep,
        "channel": channel,
        "target_id": target,
        "yaml_written": bool(write_yaml),
        "hint": "Mettez l’actionneur en mode Learn avant l’appel. Testez ensuite switch.turn_on/off."
    }), 200

@app.post("/pair/teachin")
def pair_teachin():
    """
    Envoi direct UTE (force) sans passer par /pair/start
    Body JSON:
    {
      "target_id": "05:97:9C:FA",
      "eep": "D2-01-12",
      "channel": 0,
      "name_prefix": "Lumière - Chambre Luo"
    }
    """
    body = request.get_json(silent=True) or {}
    serial_port = opts["serial_port"]
    eep_dir     = opts["eep_dir"]
    manuf_id    = int(opts["manufacturer_id"])
    write_yaml  = bool(opts["write_yaml"])

    try:
        base_id = read_base_id(serial_port)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Base ID non lisible: {e}"}), 400

    eep  = body.get("eep", "D2-01-12")
    ch   = int(body.get("channel", 0))
    name_prefix = body.get("name_prefix", "Actionneur EnOcean")

    try:
        rorg, func, typ = load_eep(eep_dir, eep)
    except Exception as e:
        return jsonify({"ok": False, "error": f"EEP introuvable/illisible: {e}"}), 400

    target = body.get("target_id")
    if not target:
        return jsonify({"ok": False, "error": "target_id requis"}), 400

    try:
        target_id = str_id_to_bytes(target)
    except Exception as e:
        return jsonify({"ok": False, "error": f"target_id invalide: {e}"}), 400

    try:
        teachin_ute(serial_port, base_id, target_id, rorg, func, typ, manuf_id, ch)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Échec envoi UTE: {e}"}), 500

    if write_yaml:
        add_switch_dual(target, name_prefix)

    return jsonify({
        "ok": True,
        "eep": eep,
        "channel": ch,
        "target_id": target,
        "yaml_written": bool(write_yaml)
    }), 200
