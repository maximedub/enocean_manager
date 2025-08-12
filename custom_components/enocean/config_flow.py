# -*- coding: utf-8 -*-
"""
Config flow (copie simplifiée du core) :
- Permet l’ajout via l’UI (chemin du port série)
- Valide que le port est accessible
"""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .dongle import validate_path, detect

class EnOceanFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestionnaire du flow EnOcean."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Premier écran : choix du port série (ou propose détectés)."""
        errors = {}
        ports = detect() or []
        schema = vol.Schema({vol.Required(CONF_DEVICE): cv.string})

        if user_input is not None:
            if not await self.hass.async_add_executor_job(validate_path, user_input[CONF_DEVICE]):
                errors["base"] = "invalid_dongle_path"
            else:
                return self.async_create_entry(title="EnOcean", data=user_input)

        defaults = ports[0] if ports else "/dev/serial/by-id/..."
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={"ports": "\n".join(ports) if ports else "Aucun trouvé"},
            last_step=True,
        )

    @callback
    def async_get_options_flow(self, config_entry):
        """Retourne le flow d’options (pas d’options ici)."""
        return EnOceanOptionsFlow(config_entry)

class EnOceanOptionsFlow(config_entries.OptionsFlow):
    """Flow d’options vide (placeholder)."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Pas d’options spécifiques."""
        return self.async_create_entry(title="", data={})
