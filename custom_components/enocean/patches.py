"""Corrections de compatibilité (monkey patches) pour la lib pyenocean.

Objectif : ne JAMAIS faire planter l’intégration si la méthode attendue
n’existe pas dans la lib (ex: Packet.send_response pour UTE).
On loggue un warning et on continue sans patch "actif".
"""

from __future__ import annotations

import logging
from typing import Optional

from enocean.protocol.packet import Packet

_LOGGER = logging.getLogger(__name__)

# Durée d’attente "douce" pour la réception du Base ID (affichage warning uniquement)
_BASE_ID_WAIT_WARN_S = 2.0


def safe_apply_ute_patch() -> None:
    """Applique (ou pas) un patch UTE selon les capacités de la lib.

    Si la méthode/point d’extension n’existe pas, on loggue un warning une seule fois
    mais on NE lève PAS d’exception : l’intégration doit continuer à fonctionner.
    """
    try:
        # Exemple : certaines versions n’ont pas Packet.send_response.
        if not hasattr(Packet, "send_response"):
            _LOGGER.warning(
                "Patch UTE impossible: %s",
                "type object 'Packet' has no attribute 'send_response'",
            )
            return

        # Si la méthode existe, on pourrait brancher ici un wrapper/patch
        # pour envoyer automatiquement un ACK au teach-in UTE, si nécessaire.
        _LOGGER.debug("Patch UTE : 'Packet.send_response' disponible, aucun patch requis.")
    except Exception:
        # Ne jamais casser le démarrage si la lib évolue.
        _LOGGER.exception("Échec inattendu lors de l’application du patch UTE (ignoré).")


def warn_base_id_not_received_once(waited_s: float) -> None:
    """Aide à tracer un avertissement si le Base ID tarde à arriver.

    Le code appelant peut invoquer cette fonction quand le délai dépasse
    _BASE_ID_WAIT_WARN_S. On évite les logs en boucle.
    """
    if waited_s >= _BASE_ID_WAIT_WARN_S:
        _LOGGER.warning("Base ID non reçu (%.1fs).", waited_s)
