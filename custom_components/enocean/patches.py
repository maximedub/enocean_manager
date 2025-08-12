# config/custom_components/enocean/patches.py
# -*- coding: utf-8 -*-
"""
Patches de compatibilité pour python-enocean (teach-in UTE).
- Protège Packet.send_response() si le Base ID du dongle n'est pas encore connu.
- Tente de lire le Base ID (CO_RD_IDBASE) quand un communicator est fourni.
- NE se marque 'patché' QUE si le wrapper a été effectivement posé.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

_LOGGER = logging.getLogger(__name__)


def _request_base_id(communicator, timeout_s: float = 2.0) -> Optional[list[int]]:
    """Demande CO_RD_IDBASE et attend que communicator.base_id soit rempli (si le thread tourne)."""
    try:
        from enocean.protocol.packet import Packet  # import local
    except Exception as exc:
        _LOGGER.debug("CO_RD_IDBASE: import Packet impossible: %s", exc)
        return None

    try:
        # Common command (type 0x05), CO_RD_IDBASE = 0x08
        pkt = Packet(0x05, data=[0x08], optional=[])
        communicator.send(pkt)
    except Exception as exc:
        _LOGGER.debug("CO_RD_IDBASE non envoyé (communicator pas prêt ?): %s", exc)
        return None

    t0 = time.time()
    base_id = getattr(communicator, "base_id", None)
    while base_id is None and (time.time() - t0) < timeout_s:
        time.sleep(0.05)
        base_id = getattr(communicator, "base_id", None)

    if base_id is not None:
        _LOGGER.info("EnOcean Base ID: %s", base_id)
    else:
        _LOGGER.debug("Base ID non reçu après %.1fs (pas bloquant).", timeout_s)
    return base_id


def apply_enocean_workaround(communicator=None) -> None:
    """
    Applique un wrapper tolérant autour de Packet.send_response() :
    - Si base_id inconnu -> on N'ENVOIE PAS la réponse UTE (évite le crash).
    - Sinon -> on appelle la méthode d'origine.
    Appelée par le code du dongle avec le communicator (si dispo).
    """
    try:
        from enocean.protocol.packet import Packet  # import local pour patcher la vraie classe
    except Exception as exc:
        _LOGGER.warning("Patch UTE non appliqué (import Packet impossible): %s", exc)
        # pas de flag "patché" ici
        return

    # Si déjà patché, on ne refait pas (mais UNIQUEMENT si on a déjà vraiment patché)
    if getattr(Packet, "_ha_enocean_patched", False):
        return

    if not hasattr(Packet, "send_response"):
        # Certaines versions n'exposent pas send_response : on log et on sort SANS marquer patché.
        _LOGGER.warning("Patch UTE: Packet.send_response() absent sur cette version de python-enocean.")
        return

    _orig_send_response = Packet.send_response  # sauvegarde

    def _safe_send_response(self):  # type: ignore[override]
        """N'envoie une réponse UTE que si le Base ID est connu, sinon ignore proprement."""
        try:
            communicator = getattr(self, "_Packet__communicator", None)
            base_id = getattr(communicator, "base_id", None) if communicator else None
            if not base_id:
                _LOGGER.warning(
                    "UTE: base_id du dongle inconnu au moment du teach-in, réponse ignorée."
                )
                return
            return _orig_send_response(self)
        except Exception as exc:
            _LOGGER.exception("UTE: erreur protégée lors de send_response: %s", exc)

    # Application effective du patch
    Packet.send_response = _safe_send_response  # type: ignore[assignment]
    setattr(Packet, "_ha_enocean_patched", True)
    _LOGGER.debug("Patch UTE appliqué: send_response() sécurisé.")

    # Si on nous fournit le communicator, on tente aussi de récupérer le Base ID
    if communicator is not None:
        try:
            _request_base_id(communicator, timeout_s=2.0)
        except Exception:
            _LOGGER.exception("Lecture du Base ID échouée (ignorée).")
