import time
import threading
import os
from enocean.protocol.packet import RadioPacket
from devices import save_device
from communicator import communicator

EEP_XML_DIRECTORY = "/app/eep"
SENDER_ID = communicator.sender_id

def send_pairing_signal(target_id):
    for _ in range(3):
        communicator.send(RadioPacket.create_packet(rorg=0xF6, sender=SENDER_ID, destination=target_id, data=[0x70]))
        time.sleep(0.1)
        communicator.send(RadioPacket.create_packet(rorg=0xF6, sender=SENDER_ID, destination=target_id, data=[0x00]))
        time.sleep(0.1)

def appairer_auto(callback=None):
    import logging
    logging.info("🔍 En attente d'une trame pour appairage...")
    communicator._buffer.clear()

    while True:
        packet = communicator.receive()
        if packet and hasattr(packet, 'sender_hex'):
            sender_id = packet.sender
            data = list(packet.data)
            rorg = packet.rorg
            eep_func = data[0] if len(data) > 0 else 0x00
            eep_type = data[1] if len(data) > 1 else 0x00

            eep_info = find_matching_eep_file(rorg, eep_func, eep_type)

            save_device(sender_id)

            result = {
                "target_id": sender_id,
                "eep_code": eep_info.get("eep"),
                "eep_file": eep_info.get("file") if eep_info.get("status") == "found" else None,
                "message": eep_info.get("message"),
                "status": eep_info.get("status")
            }

            if callback:
                callback(result)

            return result

def find_matching_eep_file(rorg, func, type_):
    """Recherche un fichier XML de type D2-XX-YY dans le répertoire /app/eep"""
    eep_code = f"D2-{func:02X}-{type_:02X}"
    filename = f"{eep_code}.xml"
    path = os.path.join(EEP_XML_DIRECTORY, filename)
    if os.path.exists(path):
        return {
            "status": "found",
            "eep": eep_code,
            "file": filename,
            "path": path
        }
    else:
        return {
            "status": "missing",
            "eep": eep_code,
            "message": f"Fichier EEP XML manquant : {filename}"
        }
