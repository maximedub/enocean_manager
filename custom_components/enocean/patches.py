# custom_components/enocean/patches.py
from __future__ import annotations
import logging

from enocean.protocol.packet import Packet

_LOGGER = logging.getLogger(__name__)

def apply_enocean_workaround() -> None:
    """Appliquer des contournements si nécessaire pour certaines versions de py-enocean."""
    # Dans certaines versions, Packet n'a pas send_response; ce n'est pas bloquant.
    if not hasattr(Packet, "send_response"):
        _LOGGER.debug("py-enocean: send_response() indisponible (pas bloquant).")
