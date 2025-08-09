# app.py
import os
from flask import Flask, jsonify, render_template
from enocean_manager.communicator import communicator
from enocean_manager.devices import get_devices
from enocean_manager.eep import EEPRegistry

app = Flask(__name__, template_folder="templates")
_registry = EEPRegistry()

@app.route("/")
def index():
    return render_template("index.html", devices=get_devices())

@app.route("/etat")
def etat():
    return jsonify({"status": "Actif", "port": communicator.port})

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
