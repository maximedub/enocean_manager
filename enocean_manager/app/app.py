# app.py
import os
from flask import Flask, jsonify, render_template
from communicator import communicator
from devices import get_devices
from eep import EEPRegistry

app = Flask(__name__, template_folder="templates")

# Démarre l’écoute série (thread interne)
communicator.start()

@app.route("/")
def index():
    # UI optionnelle (si templates/index.html existe)
    devices = get_devices()
    return render_template("index.html", devices=devices)

@app.route("/etat", methods=["GET"])
def etat():
    return jsonify({
        "status": "Actif",
        "port": communicator.port,
        "sender_id": getattr(communicator, "sender_id", None),
    })

@app.route("/devices", methods=["GET"])
def list_devices():
    return jsonify(get_devices())

@app.route("/eep/<code>", methods=["GET"])
def get_eep(code: str):
    try:
        reg = EEPRegistry(os.environ.get("EEP_JSON_DIR"))
        profile = reg.load(code)
        return jsonify({
            "code": profile.code,
            "rorg": profile.rorg,
            "func": profile.func,
            "type": profile.type,
            "description": profile.description,
            "commands": profile.get_supported_commands(),
            "states": profile.get_supported_states(),
            "parameters": profile.get_parameters(),
            "teach_in": profile.get_teach_in_info(),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8099")))
