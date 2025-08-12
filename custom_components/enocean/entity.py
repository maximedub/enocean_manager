# -*- coding: utf-8 -*-
"""
Classe de base pour les entités EnOcean.
- S’abonne aux paquets reçus
- Filtre sur sender (dev_id)
- Méthode utilitaire d’envoi
"""

from enocean.protocol.packet import Packet
from enocean.utils import combine_hex
from homeassistant.helpers.dispatcher import async_dispatcher_connect, dispatcher_send
from homeassistant.helpers.entity import Entity

from .const import SIGNAL_RECEIVE_MESSAGE, SIGNAL_SEND_MESSAGE

class EnOceanEntity(Entity):
    """Parent commun des entités EnOcean (reprend le core)."""

    def __init__(self, dev_id: list[int]) -> None:
        """Sauve l’ID destination (récepteur)."""
        self.dev_id = dev_id

    async def async_added_to_hass(self) -> None:
        """S’abonne aux paquets radio reçus."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_RECEIVE_MESSAGE, self._message_received_callback
            )
        )

    def _message_received_callback(self, packet):
        """Appelé pour chaque paquet : filtre sur sender == dev_id."""
        if packet.sender_int == combine_hex(self.dev_id):
            self.value_changed(packet)

    def value_changed(self, packet):
        """À surcharger en plateforme : met à jour l’état suivant le paquet."""

    def send_command(self, data, optional, packet_type):
        """Construit et envoie un Packet via le dongle."""
        packet = Packet(packet_type, data=data, optional=optional)
        dispatcher_send(self.hass, SIGNAL_SEND_MESSAGE, packet)
