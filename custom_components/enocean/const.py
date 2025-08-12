# -*- coding: utf-8 -*-
"""Constantes de l’intégration EnOcean (custom)."""
import logging
from homeassistant.const import Platform

DOMAIN = "enocean"
DATA_ENOCEAN = "enocean"
ENOCEAN_DONGLE = "dongle"

# Signaux dispatcher (comme le core)
SIGNAL_RECEIVE_MESSAGE = "enocean.receive_message"
SIGNAL_SEND_MESSAGE = "enocean.send_message"

LOGGER = logging.getLogger(__package__)

# Plateformes supportées (comme le core)
PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.SWITCH,
]
