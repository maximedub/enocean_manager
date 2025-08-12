# custom_components/enocean/dongle.py
# -*- coding: utf-8 -*-
"""
dongle.py — Outils autour du communicateur série EnOcean.

- Applique le patch UTE dès l'import du module (avant toute réception).
- Expose detect() et validate_path() pour le config_flow.
- Fournit des helpers pour initialiser/arrêter le communicateur si besoin.

Ce fichier est importé très tôt par l'intégration → le patch est actif
avant que le thread de lecture ne traite un teach-in UTE.
"""

from __future__ import annotations

import glob
import logging
import os
from typing import List, Optional

from enocean.communicators import SerialCommunicator  # type: ignore

from .patches import apply_enocean_workaround

_LOGGER = logging.getLogger(__name__)

# --- Appliquer le patch UTE le plus tôt possible (aucun communicator pour l’instant) ---
try:
    apply_enocean_workaround(None)  # active le wrapper Packet.send_response() avant tout
except Exception:  # protection extrême : on ne doit jamais planter ici
    _LOGGER.exception("Échec application patch UTE à l'import (ignoré).")


# ---------- Détection / validation port ----------
def detect() -> List[str]:
    """Retourne une liste de ports série candidats (meilleure 1re valeur en tête)."""
    # by-id d'abord (stable), puis ttyUSB/ttyACM, puis ttyAMA
    patterns = [
        "/dev/serial/by-id/*",
        "/dev/ttyUSB*",
        "/dev/ttyACM*",
        "/dev/ttyAMA*",
    ]
    found: List[str] = []
    for pat in patterns:
        for p in sorted(glob.glob(pat)):
            if p not in found:
                found.append(p)
    return found


def validate_path(path: str) -> bool:
    """Valide sommairement le chemin du dongle (existence & droits)."""
    try:
        if not path:
            return False
        if not os.path.exists(path):
            return False
        # Lecture simple de stat pour vérifier les droits
        os.stat(path)
        return True
    except Exception as exc:
        _LOGGER.debug("validate_path(%s) -> False (%s)", path, exc)
        return False


# ---------- Helpers optionnels pour le communicator ----------
def init_communicator(device: str) -> SerialCommunicator:
    """
    Construit le communicateur et applique le patch AVANT le start.
    Après le start, on redemande le Base ID via apply_enocean_workaround(communicator).
    """
    comm = SerialCommunicator(port=device)  # crée le communicator
    # Patch déjà actif (appel à l'import), on peut démarrer
    comm.start()
    # Tentative lecture Base ID (idempotent et sûr)
    try:
        apply_enocean_workaround(comm)
    except Exception:
        _LOGGER.exception("Lecture du Base ID (post-start) échouée (ignorée).")
    return comm


def stop_communicator(comm: SerialCommunicator) -> None:
    """Arrête proprement le communicateur."""
    try:
        comm.stop()
    except Exception:
        _LOGGER.exception("Arrêt communicateur échoué (ignoré).")
