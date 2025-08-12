# -*- coding: utf-8 -*-
"""
Rustines : lecture rapide du Base ID + garde-fou send_response() UTE.
"""

from __future__ import annotations
import time
import logging
from typing import Optional
from enocean.protocol.packet import Packet  # type: ignore

_LOGGER = logging.getLogger(__name__)

def _request_base_id(communicator, timeout_s: float = 2.0) -> Optional[list[int]]:
    """Demande CO_RD_IDBASE et attend que communicator.base_id soit peuplé."""
    try:
        pkt = Packet(0x05, data=[0x08], optional=[])  # Common Command: CO_RD_IDBASE
        communicator.send(pkt)
    except Exception as err:
        _LOGGER.warning("CO_RD_IDBASE impossible: %s", err)

    t0 = time.time()
    while getattr(communicator, "base_id", None) is None and (time.time() - t0) < timeout_s:
        time.sleep(0.05)

    base_id = getattr(communicator, "base_id", None)
    if base_id is not None:
        _LOGGER.info("EnOcean Base ID initialisé: %s", base_id)
    else:
        _LOGGER.warning("Base ID non reçu (%.1fs).", timeout_s)
    return base_id

def _patch_send_response_guard():
    """Évite le crash si Base ID inconnu au moment d'un UTE (send_response)."""
    try:
        original = Packet.send_response

        def safe_send_response(self):
            try:
                communicator = getattr(self, "_Packet__communicator", None)
                base_id = getattr(communicator, "base_id", None) if communicator else None
                if base_id is None:
                    _LOGGER.debug("UTE ignoré (Base ID inconnu).")
                    return
                return original(self)
            except Exception as e:
                _LOGGER.exception("Exception protégée send_response(): %s", e)

        if getattr(Packet.send_response, "__name__", "") != "safe_send_response":
            Packet.send_response = safe_send_response  # type: ignore
            _LOGGER.debug("Garde-fou UTE appliqué.")
    except Exception as err:
        _LOGGER.warning("Patch UTE impossible: %s", err)

def apply_enocean_workaround(communicator) -> None:
    """Appelé après start(): garde-fou UTE + lecture Base ID."""
    _patch_send_response_guard()
    _request_base_id(communicator, timeout_s=2.0)
