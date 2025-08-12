# config/custom_components/enocean/association.py
# -*- coding: utf-8 -*-
"""
association.py — Gestion de l'association (teach-in) et d'envois D2 simples.

Ce module fournit une classe AssociationManager utilisée par __init__.py :
- listen_once(timeout, respond_ute): écoute un teach-in puis s'arrête (alias de listen).
- listen(timeout, respond_ute): idem, version "canonique" (bloquante côté thread exécuteur).
- stop_listen(): coupe l'écoute et libère le callback.
- d2_teach_in(receiver_id, channel, action, repeats): envoie un D2-01 (ON/OFF) minimal.

Notes:
- Le code est prévu pour être appelé via hass.async_add_executor_job(...) depuis __init__.py
  afin de ne JAMAIS bloquer la boucle événementielle d’Home Assistant.
- On gère proprement la pose/retrait du receive_callback du communicator.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from enocean.protocol.packet import RadioPacket, Packet  # type: ignore
from enocean.protocol.constants import PACKET  # type: ignore
from enocean.communicators import SerialCommunicator  # type: ignore

_LOGGER = logging.getLogger(__name__)

# Nom d’évènement HA publié à la détection d’un teach-in (utile pour debogage/automations).
EVENT_ENOCEAN_ID_DISCOVERED = "enocean_association_found"


class AssociationManager:
    """Pilote l'écoute teach-in et l'envoi D2-01."""

    def __init__(self, hass, communicator: SerialCommunicator) -> None:
        # Référence au core HA (pour bus d'évènements)
        self.hass = hass
        # Communicator EnOcean actif (déjà démarré par l’intégration)
        self._comm = communicator
        # Drapeau d’écoute en cours
        self._listening = False

    # ---------------------------------------------------------------------
    # API attendue par __init__.py
    # ---------------------------------------------------------------------
    def listen_once(self, timeout: int = 15, respond_ute: bool = True) -> None:
        """Alias conservant la signature attendue par __init__.py."""
        # On délègue à la méthode canonique 'listen'
        self.listen(timeout=timeout, respond_ute=respond_ute)

    # ---------------------------------------------------------------------
    # ÉCOUTE TEACH-IN
    # ---------------------------------------------------------------------
    def listen(self, timeout: int = 15, respond_ute: bool = True) -> None:
        """
        Écoute le prochain teach-in reçu par le dongle, publie un évènement HA,
        tente une réponse UTE si possible, puis s’arrête.
        Bloque le thread appelant jusqu’à réception ou expiration du délai.
        """
        if self._listening:
            _LOGGER.debug("Association: écoute déjà en cours, on ignore la nouvelle demande.")
            return

        self._listening = True
        deadline = time.time() + max(1, int(timeout))

        def _on_packet(pkt: Packet) -> None:
            """Callback interne appelé par le communicator pour chaque trame radio."""
            if not self._listening:
                return

            # On filtre les trames radio
            if isinstance(pkt, RadioPacket) and pkt.rorg is not None:
                # Récupération tolérante des infos utiles (peut varier selon la lib)
                try:
                    sender = list(pkt.sender) if hasattr(pkt, "sender") else None
                    raw = list(pkt.data) if hasattr(pkt, "data") else None
                except Exception:
                    sender, raw = None, None

                # On notifie Home Assistant via le bus d'évènements (debug/automation possible)
                try:
                    self.hass.bus.async_fire(
                        EVENT_ENOCEAN_ID_DISCOVERED,
                        {"sender": sender, "rorg": int(pkt.rorg), "raw": raw},
                    )
                except Exception:
                    # On ne casse jamais l’écoute pour un souci d’évènement
                    _LOGGER.exception("Association: échec publication d’évènement HA (ignoré).")

                _LOGGER.info("Association: teach-in détecté (sender=%s rorg=0x%02X).", sender, int(pkt.rorg))

                # Tentative de réponse UTE si la lib le permet
                if respond_ute and hasattr(pkt, "send_response"):
                    try:
                        pkt.send_response()  # certaines versions de python-enocean l'exposent
                        _LOGGER.info("Association: réponse UTE envoyée.")
                    except Exception as exc:
                        _LOGGER.warning("Association: échec réponse UTE: %s", exc)
                else:
                    if respond_ute:
                        _LOGGER.debug("Association: send_response() non dispo dans cette version de python-enocean.")

                # On a traité un teach-in → on arrête l’écoute
                self.stop_listen()

        # Armement du callback de réception
        self._comm.receive_callback = _on_packet
        _LOGGER.info(
            "Association: écoute teach-in démarrée pour %ss (respond_ute=%s).",
            timeout,
            respond_ute,
        )

        # Petite boucle d'attente (non-async, on est dans un thread d'executor)
        try:
            while self._listening and time.time() < deadline:
                time.sleep(0.05)
        finally:
            # Si on a expiré sans recevoir, on libère proprement
            if self._listening:
                _LOGGER.info("Association: fin d’écoute (timeout %ss), aucun teach-in reçu.", timeout)
                self.stop_listen()

    def stop_listen(self) -> None:
        """Coupe l’écoute teach-in et libère le callback communicator."""
        if not self._listening:
            return
        self._listening = False
        # On retire le callback pour ne pas interférer avec le fonctionnement normal
        try:
            if getattr(self._comm, "receive_callback", None) is not None:
                self._comm.receive_callback = None
        finally:
            _LOGGER.debug("Association: écoute arrêtée et callback libéré.")

    # ---------------------------------------------------------------------
    # ENVOI D2-01 (ON/OFF) — utile pendant LRN de certains actionneurs
    # ---------------------------------------------------------------------
    def d2_teach_in(
        self,
        receiver_id: list[int],
        channel: int = 0,
        action: str = "on",
        repeats: int = 2,
    ) -> None:
        """
        Envoie une trame D2-01-12 de type switching (ON/OFF) à un récepteur.
        - receiver_id: liste de 4 octets [0xAA, 0xBB, 0xCC, 0xDD]
        - channel: 0..15
        - action: "on" | "off"
        - repeats: 1..5 (répétitions durant la fenêtre LRN)
        """
        if len(receiver_id) != 4:
            raise ValueError("receiver_id doit contenir exactement 4 octets.")

        # Normalisations et garde-fous
        repeats = max(1, min(5, int(repeats)))
        ch = max(0, min(15, int(channel)))
        state = 0x01 if str(action).lower() == "on" else 0x00

        # Données minimalistes pour D2-01-12 (switching)
        # Format (simplifié) : [0xD2, 0x01, 0x12, <reserved>, <state>, <reserved>, <channel>]
        data = bytearray([0xD2, 0x01, 0x12, 0x00, state, 0x00, ch & 0x0F])
        # Optionnel : destination = ID du récepteur
        optional = bytearray(receiver_id)

        # Construction du paquet radio
        pkt = Packet(PACKET.RADIO, data=data, optional=optional)

        # Envois successifs
        for i in range(repeats):
            self._comm.send(pkt)
            _LOGGER.debug(
                "Association: D2 teach-in %s envoyé (%d/%d) vers %s (ch=%d).",
                action,
                i + 1,
                repeats,
                receiver_id,
                ch,
            )
            time.sleep(0.05)
