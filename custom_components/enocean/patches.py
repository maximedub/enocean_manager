"""
Patches de compatibilité pour la lib python-enocean (mode UTE/teach-in).

- Empêche l'envoi d'une réponse UTE si le dongle n'a pas encore de base_id
  (évitant le crash "can only concatenate list (not 'NoneType') to list").
- La fonction accepte un argument `communicator` pour correspondre à l'appel
  depuis dongle.py, même si on ne l'utilise pas directement ici.
"""

from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)


def apply_enocean_workaround(_communicator) -> None:
    """
    Applique des monkey-patches *idempotents* sur Packet.

    Signature volontairement `(communicator)` car appelée ainsi par Home Assistant :
        hass.async_add_executor_job(apply_enocean_workaround, communicator)
    """

    try:
        # Import local pour ne pas casser l'import si la lib n'est pas dispo au chargement.
        from enocean.protocol.packet import Packet  # type: ignore
    except Exception as exc:  # pragma: no cover
        _LOGGER.warning("Patch UTE non appliqué (import Packet impossible): %s", exc)
        return

    # Évite de patcher plusieurs fois si HA redémarre / re-charge.
    if getattr(Packet, "_ha_enocean_patched", False):
        return

    # --- Patch: sécuriser l'envoi de la réponse UTE tant que base_id n'est pas connu ---
    if not hasattr(Packet, "send_response"):
        _LOGGER.warning(
            "Patch UTE impossible: Packet.send_response introuvable sur cette version de python-enocean."
        )
        # On marque tout de même pour éviter de spammer les logs à chaque boot.
        setattr(Packet, "_ha_enocean_patched", True)
        return

    _orig_send_response = Packet.send_response  # sauvegarde de la méthode d'origine

    def _safe_send_response(self):  # type: ignore[override]
        """
        Wrapper tolérant :
        - Si le communicator/base_id n'est pas encore disponible → on n'envoie pas la réponse.
        - Sinon, on appelle la méthode d'origine.
        """
        try:
            communicator = getattr(self, "_Packet__communicator", None)
            base_id = getattr(communicator, "base_id", None) if communicator else None
            if not base_id:
                _LOGGER.warning(
                    "UTE: base_id du dongle inconnu au moment du teach-in, réponse ignorée (sera OK au prochain essai)."
                )
                return
            return _orig_send_response(self)
        except Exception as exc:
            _LOGGER.exception("UTE: erreur protégée lors de send_response: %s", exc)

    # Application du patch
    Packet.send_response = _safe_send_response  # type: ignore[assignment]
    setattr(Packet, "_ha_enocean_patched", True)
    _LOGGER.debug("Patch UTE appliqué (send_response sécurisé).")
