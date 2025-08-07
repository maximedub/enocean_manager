import time
import threading
from enocean.protocol.packet import RadioPacket
from app.communicator import communicator
from app.devices import save_device

# Flag pour éviter les appairages concurrents
_appairage_en_cours = False

def start_pairing():
    """Démarre un thread d'écoute pour détecter un appairage entrant"""
    global _appairage_en_cours
    if _appairage_en_cours:
        return {"status": "Appairage déjà en cours"}

    _appairage_en_cours = True

    def listen_and_pair():
        try:
            print("[Appairage] Attente de trame entrante...")
            start_time = time.time()
            while time.time() - start_time < 10:
                packet = communicator.receive.get(timeout=1.0)
                if isinstance(packet, RadioPacket) and packet.rorg == 0xF6:
                    sender_id = packet.sender_int
                    sender_hex = [int(b, 16) for b in f"{sender_id:08X}"]
                    print(f"[Appairage] Trame reçue de : {sender_hex}")
                    
                    # Sauvegarde dans la base
                    save_device(sender_hex)

                    # Réponse : envoyer 3 impulsions
                    for _ in range(3):
                        communicator.send(RadioPacket.create_packet(
                            rorg=0xF6,
                            sender=communicator.sender_id,
                            destination=sender_hex,
                            data=[0x70]
                        ))
                        time.sleep(0.1)
                        communicator.send(RadioPacket.create_packet(
                            rorg=0xF6,
                            sender=communicator.sender_id,
                            destination=sender_hex,
                            data=[0x00]
                        ))
                        time.sleep(0.1)

                    print("[Appairage] Trame d’appairage envoyée.")
                    break
        except Exception as e:
            print(f"[Appairage] Erreur : {e}")
        finally:
            global _appairage_en_cours
            _appairage_en_cours = False

    threading.Thread(target=listen_and_pair, daemon=True).start()
    return {"status": "Appairage lancé"}

