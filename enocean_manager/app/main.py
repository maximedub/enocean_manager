from flask import Flask, jsonify, render_template
from enocean.communicators.serialcommunicator import SerialCommunicator
from enocean.protocol.packet import RadioPacket
import threading, os, json, time

app = Flask(__name__, template_folder="templates")

PORT = '/dev/serial/by-id/usb-EnOcean_GmbH_EnOcean_USB_300_DC_FT4T6Q61-if00-port0'
SENDER_ID = [0xFF, 0xC6, 0xEA, 0x01]
PAIRED_DEVICES_FILE = "/data/devices.json"

COMM = SerialCommunicator(port=PORT)
COMM.start()
time.sleep(1)

if not os.path.exists(PAIRED_DEVICES_FILE):
    with open(PAIRED_DEVICES_FILE, "w") as f:
        json.dump([], f)

def save_device(device):
    with open(PAIRED_DEVICES_FILE, "r+") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []
        if device not in data:
            data.append(device)
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

def get_devices():
    with open(PAIRED_DEVICES_FILE, "r") as f:
        return json.load(f)

@app.route("/")
def index():
    return render_template("index.html", devices=get_devices())

@app.route("/appairer", methods=["POST"])
def appairer():
    def detect_and_pair():
        try:
            print("[INFO] Démarrage de l’écoute pour appairage...")
            # Attendre une trame entrante pendant 10 secondes max
            for _ in range(100):  # 100 × 0.1s = 10 secondes
                if COMM.receive.get():
                    packet = COMM.receive.get(block=False)
                    if hasattr(packet, 'sender') and packet.sender:
                        sender = packet.sender.hex()
                        print(f"[INFO] Appareil détecté : {sender}")
                        save_device(sender)

                        # Trame d'appairage envoyée
                        for _ in range(3):
                            COMM.send(RadioPacket.create_packet(
                                rorg=0xF6,
                                sender=SENDER_ID,
                                destination=packet.sender,
                                data=[0x70]
                            ))
                            time.sleep(0.1)
                            COMM.send(RadioPacket.create_packet(
                                rorg=0xF6,
                                sender=SENDER_ID,
                                destination=packet.sender,
                                data=[0x00]
                            ))
                            time.sleep(0.1)
                        break
                time.sleep(0.1)
        except Exception as e:
            print(f"[ERROR] Appairage échoué : {e}")

    threading.Thread(target=detect_and_pair).start()

    # ✅ Réponse JSON valide
    return jsonify({"status": "Recherche d’un appareil en cours…"})  # <--- corrige ici


@app.route("/devices", methods=["GET"])
def list_devices():
    return jsonify(get_devices())

@app.route("/etat", methods=["GET"])
def etat():
    return jsonify({"status": "Actif", "port": PORT, "sender_id": SENDER_ID})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
