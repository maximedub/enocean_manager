from flask import Flask, jsonify, render_template
from app.communicator import communicator
from app.pairing import start_pairing_listener
from app.devices import get_devices
from app.eep_parser import download_eep_file, parse_eep_file

app = Flask(__name__, template_folder="templates")

# Initialisation du communicateur série (thread en arrière-plan)
communicator.start()

# Lancement du thread de détection des trames Teach-In
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
        "sender_id": communicator.sender_id,
        "eep_fichier": download_eep_file(local_only=True)
    })

@app.route("/download-eep", methods=["GET"])
def download_eep():
    try:
        success = download_eep_file()
        return jsonify({"status": "OK" if success else "Erreur"})
    except Exception as e:
        return jsonify({"status": "Erreur", "error": str(e)}), 500

@app.route("/parse-eep", methods=["GET"])
def parse_eep():
    try:
        result = parse_eep_file()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/devices", methods=["GET"])
def list_devices():
    return jsonify(get_devices())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

