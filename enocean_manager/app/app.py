# app/app.py
from flask import Flask, jsonify, render_template
from enocean_manager.communicator import communicator
from enocean_manager.pairing import start_pairing_listener  # si tu as une fonction; sinon adapte
from enocean_manager.devices import get_devices
from enocean_manager.eep_parser import download_eep_file, parse_eep_file

app = Flask(__name__, template_folder="templates")

communicator.start()
start_pairing_listener()

@app.route("/")
def index():
    devices = get_devices()
    return render_template("index.html", devices=devices)

@app.route("/etat", methods=["GET"])
def etat():
    return jsonify({
        "status": "Actif",
        "port": communicator.port,
        "sender_id": getattr(communicator, "sender_id", None),
        "eep_fichier": download_eep_file(local_only=True)
    })

@app.route("/download-eep", methods=["GET"])
def download_eep():
    ok_path = download_eep_file()
    return jsonify({"status": "OK", "path": ok_path})

@app.route("/parse-eep", methods=["GET"])
def parse_eep():
    return jsonify(parse_eep_file())

@app.route("/devices", methods=["GET"])
def list_devices():
    return jsonify(get_devices())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

