# -*- coding: utf-8 -*-
"""
Intégration EnOcean (custom) : identique au core, avec dongle patché.
- Supporte l'import YAML (enocean: device: /dev/serial/...)
- Crée le dongle et le démarre (voir dongle.py patché)
"""

from __future__ import annotations
import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_DEVICE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DATA_ENOCEAN, DOMAIN, ENOCEAN_DONGLE
from .dongle import EnOceanDongle  # <- dongle patché (lecture BaseID + garde UTE)

# Schéma YAML de compatibilité (même qu'en core)
CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_DEVICE): cv.string})},
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Import YAML enocean: vers une config entry (si pas déjà créée)."""
    if DOMAIN not in config:
        return True

    # Évite les doubles
    if hass.config_entries.async_entries(DOMAIN):
        return True

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=config[DOMAIN]
        )
    )
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Instancie le dongle et l’enregistre dans hass.data."""
    enocean_data = hass.data.setdefault(DATA_ENOCEAN, {})
    usb_dongle = EnOceanDongle(hass, entry.data[CONF_DEVICE])
    await usb_dongle.async_setup()
    enocean_data[ENOCEAN_DONGLE] = usb_dongle
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Nettoyage à la suppression de l’intégration."""
    enocean_dongle = hass.data[DATA_ENOCEAN][ENOCEAN_DONGLE]
    enocean_dongle.unload()
    hass.data.pop(DATA_ENOCEAN, None)
    return True
