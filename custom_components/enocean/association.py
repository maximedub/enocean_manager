# custom_components/enocean/association.py
from __future__ import annotations

import logging
import time
from typing import Optional, Callable

from enocean.protocol.packet import RadioPacket, Packet
from enocean.protocol.constants import PACKET
from enocean.communicators import SerialCommunicator

_LOGGER = logging.getLogger(__name__)

EVENT_ENOCEAN_ID_DISCOVERED = "enocean_association_found"


class AssociationManager:
    """Gère l'écoute teach-in et l'envoi d'un D2 simple."""

    def __init__(self, hass, communicator: SerialCommunicator) -> None:
        self.hass = hass
        self._comm = communicator
        self._listening = False

    # ---------- ÉCOUTE TEACH-IN ----------
    def listen(self, timeout: int = 15, respond_ute: bool = True) -> None:
        """Écoute le prochain teach-in, publie un évènement HA, et tente une réponse UTE si possible."""
        if self._listening:
            _LOGGER.debug("Déjà en écoute, on ignore la nouvelle demande.")
            return

        self._listening = True
        deadline = time.time() + max(1, int(timeout))

        def on_packet(pkt: Packet) -> None:
            if not self._listening:
                return

            if isinstance(pkt, RadioPacket) and pkt.rorg is not None:
                try:
                    sender = list(pkt.sender) if hasattr(pkt, "sender") else None
                    raw = list(pkt.data) if hasattr(pkt, "data") else None
                except Exception:
                    sender, raw = None, None

                # Évènement côté HA (dev tools -> Events)
                self.hass.bus.async_fire(
                    EVENT_ENOCEAN_ID_DISCOVERED,
                    {"sender": sender, "rorg": int(pkt.rorg), "raw": raw},
                )

                _LOGGER.info("Teach-in détecté: sender=%s rorg=0x%02X", sender, int(pkt.rorg))

                # Tentative de réponse UTE si supporté par la lib
                if respond_ute and hasattr(pkt, "send_response"):
                    try:
                        pkt.send_response()  # certaines versions de py-enocean proposent cette méthode
                        _LOGGER.info("Réponse UTE envoyée via pkt.send_response()")
                    except Exception as exc:
                        _LOGGER.warning("Échec envoi réponse UTE: %s", exc)
                else:
                    if respond_ute:
                        _LOGGER.debug("send_response() non disponible dans cette version de py-enocean; on continue sans répondre.")

                # On s’arrête après le premier teach-in
                self.stop_listen()

        self._comm.receive_callback = on_packet
        _LOGGER.info("Écoute teach-in démarrée pour %ss (respond_ute=%s)", timeout, respond_ute)

        # Boucle d'attente simple (bloquante côté thread communicateur)
        while self._listening and time.time() < deadline:
            time.sleep(0.05)

        if self._listening:
            _LOGGER.info("Fin de fenêtre d’écoute (%ss), aucun teach-in reçu.", timeout)
            self.stop_listen()

    def stop_listen(self) -> None:
        """Arrête l’écoute teach-in."""
        if not self._listening:
            return
        self._listening = False
        # Libère le callback
        self._comm.receive_callback = None
        _LOGGER.debug("Écoute teach-in arrêtée.")

    # ---------- ENVOI D2-01 (ON/OFF) ----------
    def d2_teach_in(self, receiver_id: list[int], channel: int = 0, action: str = "on", repeats: int = 2) -> None:
        """
        Envoie une trame D2-01 (ON/OFF) à un récepteur.
        receiver_id: [0xAA,0xBB,0xCC,0xDD]
        channel: 0..15
        action: "on" | "off"
        """
        if len(receiver_id) != 4:
            raise ValueError("receiver_id doit contenir 4 octets")

        repeats = max(1, min(5, int(repeats)))
        ch = max(0, min(15, int(channel)))
        state = 0x01 if str(action).lower() == "on" else 0x00

        # D2-01-12 : CMD = 0x01 (switching) / 0x02 (dimming). Ici, simple ON/OFF switching.
        # Données minimalistes: [CMD, output_value, reserved, ch]
        data = bytearray([0xD2, 0x01, 0x12, 0x00, state, 0x00, ch & 0x0F])
        optional = bytearray(receiver_id)  # destination

        pkt = Packet(PACKET.RADIO, data=data, optional=optional)
        for i in range(repeats):
            self._comm.send(pkt)
            _LOGGER.debug("D2 teach-in %s envoyé (%d/%d) vers %s (ch=%d)", action, i + 1, repeats, receiver_id, ch)
            time.sleep(0.05)
