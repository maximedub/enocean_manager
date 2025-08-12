# -*- coding: utf-8 -*-
"""
Rustines de robustesse :
- Demande explicite du Base ID à chaud (CO_RD_IDBASE) pour peupler communicator.base_id
- Garde-fou sur send_response() pour éviter le crash UTE si base_id == None
"""

from __future__ import annotations
import time
import logging
from typing import Optional

from enocean.protocol.packet import Packet  # type: ignore

_LOGGER = logging.getLogger(__name__)

def _request_base_id(communicator, timeout_s: float = 2.0) -> Optional[list[int]]:
    """Envoie CO_RD_IDBASE (ESP3 0x05 / 0x08) et attend la mise à jour base_id."""
    try:
        pkt = Packet(0x05, data=[0x08], optional=[])  # Common Command: CO_RD_IDBASE
        communicator.send(pkt)
    except Exception as err:
        _LOGGER.warning("Impossible d'envoyer CO_RD_IDBASE: %s", err)

    t0 = time.time()
    while getattr(communicator, "base_id", None) is None and (time.time() - t0) < timeout_s:
        time.sleep(0.05)

    base_id = getattr(communicator, "base_id", None)
    if base_id is not None:
        _LOGGER.info("EnOcean Base ID initialisé: %s", base_id)
    else:
        _LOGGER.warning("Base ID non reçu (%.1fs). On continue quand même.", timeout_s)
    return base_id

def _patch_send_response_guard():
    """Monkey-patch Packet.send_response() pour ignorer UTE si base_id inconnu."""
    try:
        original = Packet.send_response

        def safe_send_response(self):
            try:
                communicator = getattr(self, "_Packet__communicator", None)
                base_id = getattr(communicator, "base_id", None) if communicator else None
                if base_id is None:
                    _LOGGER.debug("UTE ignoré (Base ID inconnu pour l’instant).")
                    return
                return original(self)
            except Exception as e:
                _LOGGER.exception("Exception protégée dans send_response(): %s", e)

        if getattr(Packet.send_response, "__name__", "") != "safe_send_response":
            Packet.send_response = safe_send_response  # type: ignore[assignment]
            _LOGGER.debug("Garde-fou UTE appliqué.")
    except Exception as err:
        _LOGGER.warning("Échec du garde-fou UTE: %s", err)

def apply_enocean_workaround(communicator) -> None:
    """À appeler juste après .start(): applique garde-fou + lit Base ID."""
    _patch_send_response_guard()
    _request_base_id(communicator, timeout_s=2.0)
