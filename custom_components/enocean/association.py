# -*- coding: utf-8 -*-
"""
association.py — Gestion de l'association (teach-in) côté custom component.

- Service 'association_listen' : met le dongle en écoute et détecte le prochain paquet
  intéressant (UTE / 4BS / F6). En cas de UTE, option pour répondre automatiquement.
  Publie un évènement 'enocean_association_found' avec les infos utiles.

- Service 'association_d2_teach' : envoie D2-01 ON/OFF sur un canal pour permettre
  l'apprentissage d'un actionneur D2-01-xx pendant sa fenêtre LRN.

Cette 1ère version ne tente pas encore de "reconnaître" l'EEP dans nos JSON ;
on y viendra en étape 2 en important un petit index EEP (RORG-FUNC-TYPE → libellé).
"""

from __future__ import annotations
import time
import threading
import logging
from dataclasses import dataclass
from typing import Callable, Optional, List

from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import dispatcher_send

from enocean.protocol.packet import Packet, RadioPacket  # type: ignore

from .const import SIGNAL_SEND_MESSAGE

_LOGGER = logging.getLogger(__name__)

# --- Quelques constantes RORG utiles ---
RORG_UTE = 0xD4  # Universal Teach-In
RORG_4BS = 0xA5  # 4BS (peut contenir teach-in selon EEP)
RORG_RPS = 0xF6  # Rocker (pas de teach-in 'standard', mais on capte l'ID)

@dataclass
class ListenResult:
    """Conteneur pour le résultat de l'écoute."""
    sender: List[int]     # ID émetteur (4 octets)
    rorg: int             # RORG détecté
    raw: List[int]        # Données brutes (data + optional utiles)
    description: str      # Texte court (explicatif)

class AssociationManager:
    """Gère une session d'écoute teach-in et l'envoi de paquets D2."""

    def __init__(self, hass: HomeAssistant, communicator) -> None:
        """Garde les poignées vers hass et le communicator py-enocean."""
        self.hass = hass
        self._communicator = communicator
        self._lock = threading.Lock()
        self._listening = False

    # --------------------- ÉCOUTE / DÉTECTION ---------------------

    def _is_teach_in_candidate(self, pkt: RadioPacket) -> bool:
        """Heuristique simple : UTE (D4) toujours ; 4BS (A5) et F6 (F6) acceptés aussi."""
        try:
            rorg = pkt.data[0]
            return rorg in (RORG_UTE, RORG_4BS, RORG_RPS)
        except Exception:
            return False

    def _packet_to_result(self, pkt: RadioPacket) -> ListenResult:
        """Transforme un RadioPacket en résultat exploitable pour l’UI."""
        sender = list(pkt.sender) if isinstance(pkt.sender, (bytes, bytearray)) else pkt.sender
        rorg = pkt.data[0]
        # On expose 'data' et 'optional' concaténés pour debug/interop
        raw = list(pkt.data) + list(pkt.optional or [])
        if rorg == RORG_UTE:
            desc = "Teach-in UTE détecté (réponse possible)"
        elif rorg == RORG_4BS:
            desc = "Télégramme 4BS détecté (peut contenir teach-in selon EEP)"
        elif rorg == RORG_RPS:
            desc = "Télégramme RPS (rocker) détecté"
        else:
            desc = "Télégramme radio détecté"
        return ListenResult(sender=sender, rorg=rorg, raw=raw, description=desc)

    def listen_once(self, timeout_s: int = 15, respond_ute: bool = True) -> Optional[ListenResult]:
        """Bloque jusqu'au 1er paquet 'candidat' ou timeout, puis retourne le résultat.

        NOTE: Appelé dans un thread d'executor (pas dans l'event loop).
        """
        with self._lock:
            if self._listening:
                _LOGGER.warning("Session d'écoute déjà en cours.")
                return None
            self._listening = True
        try:
            deadline = time.time() + max(1, timeout_s)
            while time.time() < deadline:
                pkt = self._communicator.receive(blocking=True, timeout=0.2)  # type: ignore[attr-defined]
                if not pkt or not isinstance(pkt, RadioPacket):
                    continue
                if not self._is_teach_in_candidate(pkt):
                    continue

                res = self._packet_to_result(pkt)
                _LOGGER.info("Association: paquet détecté rorg=0x%02X sender=%s", res.rorg, res.sender)

                # Réponse UTE facultative (accusé teach-in)
                if respond_ute and res.rorg == RORG_UTE:
                    try:
                        _LOGGER.debug("Réponse UTE -> send_response()")
                        pkt.send_response()  # notre custom a un garde-fou si base_id None
                    except Exception as e:
                        _LOGGER.warning("Échec send_response() UTE: %s", e)

                return res
            _LOGGER.info("Association: timeout (%ss) sans paquet éligible.", timeout_s)
            return None
        finally:
            with self._lock:
                self._listening = False

    # --------------------- ENVOI D2-01 (TEACH-IN ACTUATEUR) ---------------------

    def send_d2_01(self, target_id: List[int], channel: int, on: bool, repeats: int = 2) -> None:
        """Construit et envoie un D2-01 ON/OFF vers un récepteur (pendant LRN).

        - ON pendant LRN = la plupart des D2-01 apprennent l’émetteur (sender HA)
        - OFF idem, selon fabricants ; ON est plus 'universel'
        """
        # data D2-01 : D2 01 [chan] [valeur] ...
        value = 0x64 if on else 0x00  # 100% ou 0%
        data = [0xD2, 0x01, channel & 0xFF, value, 0x00, 0x00, 0x00, 0x00, 0x00]

        # optional = 'destination' (id récepteur) + flags
        optional = [0x03] + list(target_id) + [0xFF, 0x00]

        # Envoie N fois (utile pendant LRN)
        for i in range(max(1, repeats)):
            pkt = Packet(0x01, data=data, optional=optional)  # type: ignore
            dispatcher_send(self.hass, SIGNAL_SEND_MESSAGE, pkt)
            _LOGGER.debug("D2-01 %s envoyé (%d/%d) -> %s ch=%d",
                          "ON" if on else "OFF", i + 1, repeats, target_id, channel)
            time.sleep(0.15)
