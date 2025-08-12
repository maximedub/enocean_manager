# -*- coding: utf-8 -*-
"""
Dongle EnOcean patché :
- Démarre le SerialCommunicator
- Applique nos rustines (lecture Base ID + garde-fou UTE)
- Redispatche les paquets radio aux plateformes
"""

import glob
import logging
from os.path import basename, normpath

from enocean.communicators import SerialCommunicator
from enocean.protocol.packet import RadioPacket
import serial

from homeassistant.helpers.dispatcher import async_dispatcher_connect, dispatcher_send

from .const import SIGNAL_RECEIVE_MESSAGE, SIGNAL_SEND_MESSAGE
from .patches import apply_enocean_workaround

_LOGGER = logging.getLogger(__name__)

class EnOceanDongle:
    """Représentation du dongle EnOcean (presque identique au core)."""

    def __init__(self, hass, serial_path):
        """Construit le communicator série et garde le chemin pour l’UI."""
        self._communicator = SerialCommunicator(
            port=serial_path,
            callback=self.callback,
        )
        self.serial_path = serial_path
        self.identifier = basename(normpath(serial_path))
        self.hass = hass
        self.dispatcher_disconnect_handle = None

    async def async_setup(self):
        """Démarre le thread série + applique les rustines, et connecte le dispatcher."""
        # Démarre la communication série
        self._communicator.start()

        # Lit le BaseID + sécurise UTE sans bloquer l’event loop
        await self.hass.async_add_executor_job(
            apply_enocean_workaround, self._communicator
        )

        # Abonnement aux commandes sortantes
        self.dispatcher_disconnect_handle = async_dispatcher_connect(
            self.hass, SIGNAL_SEND_MESSAGE, self._send_message_callback
        )

    def unload(self):
        """Désabonnement propre au déchargement de l’intégration."""
        if self.dispatcher_disconnect_handle:
            self.dispatcher_disconnect_handle()
            self.dispatcher_disconnect_handle = None

    def _send_message_callback(self, command):
        """Envoie un Packet via le communicator (utilisé par les entités)."""
        self._communicator.send(command)

    def callback(self, packet):
        """Reçoit chaque paquet radio et le redispatche aux entités."""
        if isinstance(packet, RadioPacket):
            _LOGGER.debug("Paquet radio reçu: %s", packet)
            dispatcher_send(self.hass, SIGNAL_RECEIVE_MESSAGE, packet)

def detect():
    """Détecte des chemins de clé EnOcean courants (optionnel)."""
    globs_to_test = ["/dev/tty*FTOA2PV*", "/dev/serial/by-id/*EnOcean*"]
    found_paths = []
    for current_glob in globs_to_test:
        found_paths.extend(glob.glob(current_glob))
    return found_paths

def validate_path(path: str):
    """Retourne True si le port série est valide et accessible."""
    try:
        SerialCommunicator(port=path)
    except serial.SerialException as exception:
        _LOGGER.warning("Dongle path %s invalide: %s", path, str(exception))
        return False
    return True
