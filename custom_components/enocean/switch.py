# -*- coding: utf-8 -*-
"""
Plateforme switch EnOcean (copie core) :
- Envoie D2-01 ON/OFF vers l’ID récepteur (dev_id) + channel
- Pas de sender_id configurable (c’est normal pour D2-01)
"""

from __future__ import annotations
from typing import Any

from enocean.utils import combine_hex
import voluptuous as vol

from homeassistant.components.switch import (
    PLATFORM_SCHEMA as SWITCH_PLATFORM_SCHEMA,
    SwitchEntity,
)
from homeassistant.const import CONF_ID, CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import LOGGER, DOMAIN
from .entity import EnOceanEntity

CONF_CHANNEL = "channel"
DEFAULT_NAME = "EnOcean Switch"

# Schéma YAML : id (liste d’octets), name, channel
PLATFORM_SCHEMA = SWITCH_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ID): vol.All(cv.ensure_list, [vol.Coerce(int)]),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_CHANNEL, default=0): cv.positive_int,
    }
)

def generate_unique_id(dev_id: list[int], channel: int) -> str:
    """Construit un unique_id stable pour HA."""
    return f"{combine_hex(dev_id)}-{channel}"

def _migrate_to_new_unique_id(hass: HomeAssistant, dev_id, channel) -> None:
    """Migration héritée (compat anciennes entités)."""
    old_unique_id = f"{combine_hex(dev_id)}"
    ent_reg = er.async_get(hass)
    entity_id = ent_reg.async_get_entity_id(Platform.SWITCH, DOMAIN, old_unique_id)
    if entity_id is not None:
        new_unique_id = generate_unique_id(dev_id, channel)
        try:
            ent_reg.async_update_entity(entity_id, new_unique_id=new_unique_id)
        except ValueError:
            LOGGER.warning(
                "Skip migration of id [%s] to [%s] because it already exists",
                old_unique_id, new_unique_id
            )
        else:
            LOGGER.debug("Migrating unique_id from [%s] to [%s]", old_unique_id, new_unique_id)

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Enregistre l’entité switch depuis le YAML."""
    channel: int = config[CONF_CHANNEL]
    dev_id: list[int] = config[CONF_ID]
    dev_name: str = config[CONF_NAME]
    _migrate_to_new_unique_id(hass, dev_id, channel)
    async_add_entities([EnOceanSwitch(dev_id, dev_name, channel)])

class EnOceanSwitch(EnOceanEntity, SwitchEntity):
    """Switch D2-01 EnOcean (récepteur)."""

    _attr_is_on = False

    def __init__(self, dev_id: list[int], dev_name: str, channel: int) -> None:
        """Sauve nom/canal + unique_id."""
        super().__init__(dev_id)
        self.channel = channel
        self._attr_unique_id = generate_unique_id(dev_id, channel)
        self._attr_name = dev_name

    def turn_on(self, **kwargs: Any) -> None:
        """Envoie D2-01 ON sur le canal."""
        optional = [0x03] + self.dev_id + [0xFF, 0x00]
        self.send_command(
            data=[0xD2, 0x01, self.channel & 0xFF, 0x64, 0x00, 0x00, 0x00, 0x00, 0x00],
            optional=optional,
            packet_type=0x01,
        )
        self._attr_is_on = True

    def turn_off(self, **kwargs: Any) -> None:
        """Envoie D2-01 OFF sur le canal."""
        optional = [0x03] + self.dev_id + [0xFF, 0x00]
        self.send_command(
            data=[0xD2, 0x01, self.channel & 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
            optional=optional,
            packet_type=0x01,
        )
        self._attr_is_on = False

    def value_changed(self, packet):
        """Met à jour l’état quand on reçoit un statut D2-01."""
        if packet.data[0] == 0xA5:  # Power meter
            packet.parse_eep(0x12, 0x01)
            if packet.parsed["DT"]["raw_value"] == 1:
                raw_val = packet.parsed["MR"]["raw_value"]
                divisor = packet.parsed["DIV"]["raw_value"]
                watts = raw_val / (10 ** divisor)
                if watts > 1:
                    self._attr_is_on = True
                    self.schedule_update_ha_state()
        elif packet.data[0] == 0xD2:  # Status actuator
            packet.parse_eep(0x01, 0x01)
            if packet.parsed["CMD"]["raw_value"] == 4:
                channel = packet.parsed["IO"]["raw_value"]
                output = packet.parsed["OV"]["raw_value"]
                if channel == self.channel:
                    self._attr_is_on = output > 0
                    self.schedule_update_ha_state()
