from flask import Flask, request, jsonify, render_template
from communicator import communicator, SENDER_ID
from enocean.protocol.packet import RadioPacket
from devices import get_devices, save_device
from pairing import start_pairing_listener
from eep import load_eep_profiles
import threading
import os

app = Flask(__name__, template_folder="templates")

@app.route("/")
def index():
    return render_template("index.html", devices=get_devices())

@app.route("/appairer", methods=["POST"])
def appairer():
    # Le processus d’écoute est lancé en tâche de fond
    threading.Thread(target=start_pairing_listener, daemon=True).start()
    return jsonify({"status": "Mode appairage lancé – en attente de trame"})

@app.route("/devices", methods=["GET"])
def list_devices():
    return jsonify(get_devices())

@app.route("/etat", methods=["GET"])
def etat():
    return jsonify({
        "status": "Actif",
        "port": communicator.port,
        "sender_id": SENDER_ID
    })

@app.route("/eep", methods=["GET"])
def list_eep_profiles():
    try:
        profils = load_eep_profiles()
        return jsonify(profils)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
