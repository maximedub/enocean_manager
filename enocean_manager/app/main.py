from flask import Flask, request, jsonify, render_template
from enocean.consolelogger import init_logger
from enocean.communicators.serialcommunicator import SerialCommunicator
from enocean.protocol.packet import RadioPacket
import requests, time, threading, os
from bs4 import BeautifulSoup

app = Flask(__name__, template_folder="templates")
init_logger()

PORT = '/dev/serial/by-id/usb-EnOcean_GmbH_EnOcean_USB_300_DC_FT4T6Q61-if00-port0'
SENDER_ID = [0xFF, 0xC6, 0xEA, 0x01]
EEP_URL = "https://tools.enocean-alliance.org/EEPViewer/profiles/eep268.xml"
EEP_LOCAL_PATH = "/app/eep268.xml"

COMM = SerialCommunicator(port=PORT)
COMM.start()
time.sleep(1)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download-eep", methods=["GET"])
def download_eep():
    try:
        r = requests.get(EEP_URL)
        r.raise_for_status()
        with open(EEP_LOCAL_PATH, "wb") as f:
            f.write(r.content)
        return jsonify({"status": "Téléchargement réussi", "path": EEP_LOCAL_PATH})
    except Exception as e:
        return jsonify({"status": "Erreur", "error": str(e)}), 500

@app.route("/parse-eep", methods=["GET"])
def parse_eep():
    if not os.path.exists(EEP_LOCAL_PATH):
        return jsonify({"error": "EEP manquant"}), 404
    with open(EEP_LOCAL_PATH, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "xml")
        profiles = soup.find_all("profile")
        result = []
        for p in profiles:
            eep = p.find("eep").text if p.find("eep") else "???"
            func = p.find("functionname").text if p.find("functionname") else "???"
            result.append({"eep": eep, "function": func})
    return jsonify(result)

@app.route("/appairer", methods=["POST"])
def appairer():
    target_id = request.json.get("target_id", [0x00, 0x00, 0x00, 0x00])
    def send_pulse():
        for _ in range(3):
            COMM.send(RadioPacket.create_packet(rorg=0xF6, sender=SENDER_ID, destination=target_id, data=[0x70]))
            time.sleep(0.1)
            COMM.send(RadioPacket.create_packet(rorg=0xF6, sender=SENDER_ID, destination=target_id, data=[0x00]))
            time.sleep(0.1)
    threading.Thread(target=send_pulse).start()
    return jsonify({"status": "Appairage lancé", "target_id": target_id})

@app.route("/configurer", methods=["POST"])
def configurer():
    target_id = request.json.get("target_id", [0x00, 0x00, 0x00, 0x00])
    db0 = request.json.get("db0", 0x00)
    db1 = request.json.get("db1", 0x00)
    db2 = request.json.get("db2", 0x00)
    db3 = request.json.get("db3", 0x00)
    data = [db3, db2, db1, db0]
    packet = RadioPacket.create_packet(rorg=0xD2, sender=SENDER_ID, destination=target_id, data=data)
    COMM.send(packet)
    return jsonify({
        "status": "Configuration envoyée",
        "data": data,
        "target_id": target_id
    })

@app.route("/etat", methods=["GET"])
def etat():
    return jsonify({
        "status": "Actif",
        "port": PORT,
        "sender_id": SENDER_ID,
        "eep_fichier": os.path.exists(EEP_LOCAL_PATH)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)