# /config/custom_components/enocean/dongle.py
# -*- coding: utf-8 -*-
"""
dongle.py — Outils autour du communicateur série EnOcean + classe EnOceanDongle.

Objectifs :
- Exposer une classe EnOceanDongle (attendue par __init__.py / switch.py / light.py).
- Appliquer le patch UTE le plus tôt possible pour éviter les crashs teach-in.
- Fournir detect()/validate_path() pour le config_flow et helpers d'init/stop.

Notes :
- On commente chaque bloc pour clarifier le rôle de chaque fonction.
"""

from __future__ import annotations

import glob  # recherche des ports série candidats
import logging  # logs HA
import os  # validations de chemin
from typing import List, Optional  # annotations

from enocean.communicators import SerialCommunicator  # communicateur série EnOcean

# Patch maison : sécurise UTE (ignore l'envoi si base_id inconnu) et tente de lire le Base ID
from .patches import apply_enocean_workaround

_LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Patch UTE appliqué au plus tôt (à l'import du module)
# ---------------------------------------------------------------------------
try:
    # On active le wrapper sur Packet.send_response() avant toute réception
    apply_enocean_workaround(None)
except Exception:
    # On ne doit jamais planter à l'import
    _LOGGER.exception("Échec application patch UTE à l'import (ignoré).")


# ---------------------------------------------------------------------------
# Fonctions utilitaires de découverte/validation du port série
# ---------------------------------------------------------------------------
def detect() -> List[str]:
    """
    Retourne une liste de chemins de ports série possibles, triés par pertinence.
    - /dev/serial/by-id/* (persistant et stable)
    - /dev/ttyUSB*, /dev/ttyACM*, /dev/ttyAMA*
    """
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
    """
    Valide sommairement un chemin de dongle :
    - non vide, existe, accessible (stat ok).
    """
    try:
        if not path:
            return False
        if not os.path.exists(path):
            return False
        os.stat(path)  # Vérifie les droits d'accès
        return True
    except Exception as exc:
        _LOGGER.debug("validate_path(%s) -> False (%s)", path, exc)
        return False


# ---------------------------------------------------------------------------
# Classe EnOceanDongle — interface attendue par __init__.py & les plateformes
# ---------------------------------------------------------------------------
class EnOceanDongle:
    """
    Représente le dongle EnOcean et encapsule le SerialCommunicator.
    Fournit start()/stop(), l'accès au communicator et des utilitaires statiques.
    """

    def __init__(self, device: str) -> None:
        # Chemin du port série (ex: /dev/serial/by-id/usb-...)
        self.device = device
        # Communicator python-enocean (non démarré à la construction)
        self._comm = SerialCommunicator(port=device)

    def start(self) -> None:
        """
        Démarre le communicateur et sécurise UTE :
        - patch appliqué avant start (déjà fait à l'import par précaution)
        - start du communicator
        - tentative de lecture du Base ID (CO_RD_IDBASE) via apply_enocean_workaround(comm)
        """
        try:
            # Re-applique le patch au cas où un reload serait passé par là
            apply_enocean_workaround(None)
        except Exception:
            _LOGGER.exception("Patch UTE (pré-start) a échoué (ignoré).")

        # Démarre le thread de lecture/écriture série
        self._comm.start()

        # Lecture du Base ID (idempotent, ignore les erreurs)
        try:
            apply_enocean_workaround(self._comm)
        except Exception:
            _LOGGER.exception("Lecture du Base ID (post-start) échouée (ignorée).")

        _LOGGER.info("EnOcean dongle démarré sur %s", self.device)

    def stop(self) -> None:
        """
        Arrête proprement le communicateur (ignorer les erreurs pour ne pas bloquer HA).
        """
        try:
            self._comm.stop()
        except Exception:
            _LOGGER.exception("Arrêt du communicateur échoué (ignoré).")
        _LOGGER.info("EnOcean dongle arrêté (%s).", self.device)

    @property
    def communicator(self) -> SerialCommunicator:
        """
        Retourne l'instance SerialCommunicator active (accès lecture/envoi trames).
        """
        return self._comm

    # ---- utilitaires statiques compatibles avec d'anciens appels ----
    @staticmethod
    def detect() -> List[str]:
        """
        Proxy statique : permet d'appeler EnOceanDongle.detect() si attendu par le code.
        """
        return detect()

    @staticmethod
    def validate_path(path: str) -> bool:
        """
        Proxy statique : permet d'appeler EnOceanDongle.validate_path(...) si attendu.
        """
        return validate_path(path)


# ---------------------------------------------------------------------------
# Helpers optionnels utilisés ailleurs dans l'intégration
# ---------------------------------------------------------------------------
def init_communicator(device: str) -> SerialCommunicator:
    """
    Construit et démarre un SerialCommunicator prêt à l'emploi.
    - Applique le patch UTE pré-start
    - start()
    - Tente de lire le Base ID
    """
    dongle = EnOceanDongle(device)
    dongle.start()
    return dongle.communicator


def stop_communicator(comm: SerialCommunicator) -> None:
    """
    Arrête proprement un SerialCommunicator existant.
    """
    try:
        comm.stop()
    except Exception:
        _LOGGER.exception("Arrêt communicateur échoué (ignoré).")


# Pour expliciter les symboles exposés par ce module
__all__ = ["EnOceanDongle", "detect", "validate_path", "init_communicator", "stop_communicator"]
