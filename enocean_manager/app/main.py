from flask import Flask, request, jsonify
from enocean.consolelogger import init_logger
from enocean.communicators.serialcommunicator import SerialCommunicator
from enocean.protocol.packet import RadioPacket
import time
import threading

app = Flask(__name__)
init_logger()

PORT = '/dev/serial/by-id/usb-EnOcean_GmbH_EnOcean_USB_300_DC_FT4T6Q61-if00-port0'
SENDER_ID = [0xFF, 0xC6, 0xEA, 0x01]

COMM = SerialCommunicator(port=PORT)
COMM.start()
time.sleep(1)

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
        "sender_id": SENDER_ID
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)