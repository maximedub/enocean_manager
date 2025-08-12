# -*- coding: utf-8 -*-
"""
config_flow.py — Flux de configuration pour l'intégration custom EnOcean.

Rôles :
- Permet l'ajout via l'UI (step 'user').
- Supporte l'import YAML (step 'import') déclenché par SOURCE_IMPORT.
- Expose *au niveau du module* la fonction async_get_options_flow(config_entry)
  attendue par Home Assistant (PAS de méthode de classe du même nom).

NB : On garde la logique simple : création d'une entrée minimale. Les options
peuvent être étendues plus tard selon les besoins.
"""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN


class EnOceanFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Flux d'installation EnOcean."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Step UI : crée une entrée minimale."""
        # Une seule instance typiquement
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        return self.async_create_entry(title="EnOcean", data=user_input or {})

    async def async_step_import(self, import_data: dict | None = None) -> FlowResult:
        """Step 'import' pour prendre en charge l'import YAML."""
        # Si une entrée existe déjà, on évite les doublons
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")
        return self.async_create_entry(title="EnOcean (import YAML)", data=import_data or {})


class EnOceanOptionsFlow(config_entries.OptionsFlow):
    """Flux d'options (placeholder)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Aucune option pour l'instant — on valide directement."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Pas de formulaire pour le moment
        return self.async_create_entry(title="", data={})


# >>> IMPORTANT : fonction attendue par HA (niveau module), pas de méthode de classe du même nom !
@callback
def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
    """Retourne le flow d'options pour cette intégration."""
    return EnOceanOptionsFlow(config_entry)
