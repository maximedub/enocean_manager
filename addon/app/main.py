from flask import Flask, jsonify, render_template
from devices import get_devices
from pairing import appairer_auto
from communicator import communicator
from eep import EEPDevice

app = Flask(__name__, template_folder="templates")


@app.route("/")
def index():
    devices_raw = get_devices()
    devices = []

    for device in devices_raw:
        device_info = device.copy()
        eep_code = device.get("eep")

        if eep_code:
            try:
                eep = EEPDevice(eep_code)
                device_info["eep_info"] = eep.to_dict()
            except FileNotFoundError:
                device_info["eep_info"] = {
                    "error": f"Fichier {eep_code}.xml introuvable"
                }

        devices.append(device_info)

    return render_template("index.html", devices=devices)


@app.route("/appairer", methods=["POST"])
def appairer():
    try:
        result = appairer_auto()
        if result["status"] == "missing":
            return jsonify({
                "status": "incomplet",
                "message": result["message"],
                "target_id": result["target_id"],
                "eep_code": result["eep_code"]
            }), 404
        return jsonify({
            "status": "Appairage réussi",
            "target_id": result["target_id"],
            "eep_code": result["eep_code"],
            "eep_file": result.get("eep_file", "")
        })
    except Exception as e:
        return jsonify({"status": "Erreur", "error": str(e)}), 500



@app.route("/etat", methods=["GET"])
def etat():
    return jsonify({
        "status": "Actif",
        "port": communicator.port,
        "sender_id": communicator.sender_id
    })


@app.route("/devices", methods=["GET"])
def list_devices():
    return jsonify(get_devices())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
