# -*- coding: utf-8 -*-
"""
patches.py — Patches de compatibilité pour python-enocean (UTE/teach-in).

Rôle :
- Intercepter Packet.send_response pour éviter un crash si le dongle n'a pas encore de base_id.
- La fonction apply_enocean_workaround(communicator) *accepte 1 argument* car
  elle est appelée via hass.async_add_executor_job(apply_enocean_workaround, communicator).
"""

from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)


def apply_enocean_workaround(_communicator) -> None:
    """Applique des patchs idempotents sur Packet.send_response."""
    try:
        # Import local pour ne pas échouer au chargement du module si la lib n'est pas prête
        from enocean.protocol.packet import Packet  # type: ignore
    except Exception as exc:
        _LOGGER.warning("Patch UTE non appliqué (import Packet impossible): %s", exc)
        return

    # Évite de patcher plusieurs fois
    if getattr(Packet, "_ha_enocean_patched", False):
        return

    if not hasattr(Packet, "send_response"):
        _LOGGER.warning(
            "Patch UTE impossible: Packet.send_response introuvable sur cette version."
        )
        setattr(Packet, "_ha_enocean_patched", True)
        return

    _orig_send_response = Packet.send_response  # sauvegarde

    def _safe_send_response(self):  # type: ignore[override]
        """Wrapper tolérant si le base_id n'est pas encore connu."""
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

    Packet.send_response = _safe_send_response  # type: ignore[assignment]
    setattr(Packet, "_ha_enocean_patched", True)
    _LOGGER.debug("Patch UTE appliqué (send_response sécurisé).")
