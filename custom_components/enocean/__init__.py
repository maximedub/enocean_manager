# -*- coding: utf-8 -*-
"""
__init__.py — Intégration EnOcean (custom, patchée) + services d’association.

- Setup identique au core (dongle + dispatcher), mais on rajoute :
  * services 'association_listen' et 'association_d2_teach'
"""

from __future__ import annotations
import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_DEVICE
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DATA_ENOCEAN, DOMAIN, ENOCEAN_DONGLE
from .dongle import EnOceanDongle
from .association import AssociationManager  # <-- new

# Schéma YAML de compat (identique au core)
CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_DEVICE): cv.string})},
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Import YAML enocean: vers une config entry (si pas déjà créée)."""
    if DOMAIN not in config:
        return True
    if hass.config_entries.async_entries(DOMAIN):
        return True
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=config[DOMAIN]
        )
    )
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Instancie le dongle et enregistre les services."""
    enocean_data = hass.data.setdefault(DATA_ENOCEAN, {})
    usb_dongle = EnOceanDongle(hass, entry.data[CONF_DEVICE])
    await usb_dongle.async_setup()
    enocean_data[ENOCEAN_DONGLE] = usb_dongle

    # --- Services d’association ---
    assoc = AssociationManager(hass, usb_dongle._communicator)  # type: ignore[attr-defined]

    async def _svc_listen(call: ServiceCall):
        """Service: association_listen (écoute teach-in)."""
        timeout = int(call.data.get("timeout", 15))
        respond_ute = bool(call.data.get("respond_ute", True))

        # On passe par l'executor (receive() bloque)
        res = await hass.async_add_executor_job(assoc.listen_once, timeout, respond_ute)
        if res:
            # Publie un évènement facile à consommer dans des automatisations / UI
            hass.bus.async_fire(
                "enocean_association_found",
                {
                    "sender": res.sender,
                    "rorg": res.rorg,
                    "raw": res.raw,
                    "description": res.description,
                },
            )

    async def _svc_d2_teach(call: ServiceCall):
        """Service: association_d2_teach (envoi D2-01 ON/OFF répété)."""
        target = call.data["id"]
        channel = int(call.data.get("channel", 0))
        action = str(call.data.get("action", "on")).lower()
        repeats = int(call.data.get("repeats", 2))
        on = action != "off"
        # Executor (envoi + petites pauses)
        await hass.async_add_executor_job(assoc.send_d2_01, target, channel, on, repeats)

    hass.services.async_register(DOMAIN, "association_listen", _svc_listen)
    hass.services.async_register(DOMAIN, "association_d2_teach", _svc_d2_teach)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Nettoyage à la suppression de l’intégration."""
    enocean_dongle = hass.data[DATA_ENOCEAN][ENOCEAN_DONGLE]
    enocean_dongle.unload()
    hass.data.pop(DATA_ENOCEAN, None)

    # Désenregistrer les services pour être propre
    try:
        hass.services.async_remove(DOMAIN, "association_listen")
        hass.services.async_remove(DOMAIN, "association_d2_teach")
    except Exception:
        pass
    return True
