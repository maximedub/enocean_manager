# -*- coding: utf-8 -*-
"""
Plateforme light EnOcean (copie core) :
- Cas variateurs 4BS (A5-02-xx) avec 'sender_id' (ID émetteur simulé)
- Pas utile pour les D2-01-xx, mais on garde pour compatibilité
"""

from __future__ import annotations
import math
from typing import Any

from enocean.utils import combine_hex
import voluptuous as vol

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    PLATFORM_SCHEMA as LIGHT_PLATFORM_SCHEMA,
    ColorMode,
    LightEntity,
)
from homeassistant.const import CONF_ID, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .entity import EnOceanEntity

CONF_SENDER_ID = "sender_id"
DEFAULT_NAME = "EnOcean Light"

# Schéma YAML : sender_id requis, id optionnel (pour retours d’état)
PLATFORM_SCHEMA = LIGHT_PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_ID, default=[]): vol.All(cv.ensure_list, [vol.Coerce(int)]),
        vol.Required(CONF_SENDER_ID): vol.All(cv.ensure_list, [vol.Coerce(int)]),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Enregistre l’entité light depuis le YAML."""
    sender_id: list[int] = config[CONF_SENDER_ID]
    dev_name: str = config[CONF_NAME]
    dev_id: list[int] = config[CONF_ID]
    add_entities([EnOceanLight(sender_id, dev_id, dev_name)])

class EnOceanLight(EnOceanEntity, LightEntity):
    """Variateur EnOcean (4BS) avec brightness 0..100%."""

    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_brightness = 50
    _attr_is_on = False

    def __init__(self, sender_id: list[int], dev_id: list[int], dev_name: str) -> None:
        """Sauve le sender usurpé + id (pour status) et nom."""
        super().__init__(dev_id)
        self._sender_id = sender_id
        self._attr_unique_id = str(combine_hex(dev_id)) if dev_id else dev_name
        self._attr_name = dev_name

    def turn_on(self, **kwargs: Any) -> None:
        """Envoie 4BS (A5-02) avec brightness (1..100)."""
        if (brightness := kwargs.get(ATTR_BRIGHTNESS)) is not None:
            self._attr_brightness = brightness

        bval = math.floor(self._attr_brightness / 256.0 * 100.0)
        if bval == 0:
            bval = 1

        command = [0xA5, 0x02, bval, 0x01, 0x09]
        command.extend(self._sender_id)
        command.extend([0x00])
        self.send_command(command, [], 0x01)
        self._attr_is_on = True

    def turn_off(self, **kwargs: Any) -> None:
        """Envoie 4BS (A5-02) brightness=0."""
        command = [0xA5, 0x02, 0x00, 0x01, 0x09]
        command.extend(self._sender_id)
        command.extend([0x00])
        self.send_command(command, [], 0x01)
        self._attr_is_on = False

    def value_changed(self, packet):
        """Met à jour brightness si le device renvoie un 4BS A5-02."""
        if packet.data[0] == 0xA5 and packet.data[1] == 0x02:
            val = packet.data[2]
            self._attr_brightness = math.floor(val / 100.0 * 256.0)
            self._attr_is_on = bool(val != 0)
            self.schedule_update_ha_state()
