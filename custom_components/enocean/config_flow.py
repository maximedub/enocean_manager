"""Flux de configuration/options pour l’intégration custom EnOcean.

Ce fichier corrige la signature d'options flow afin d'éviter :
TypeError: EnOceanFlowHandler.async_get_options_flow() missing 1 required positional argument: 'config_entry'
"""

from __future__ import annotations

from typing import Any, Dict

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN


class EnOceanFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Gère le flux d'installation initial (si nécessaire)."""

    VERSION = 1

    async def async_step_user(self, user_input: Dict[str, Any] | None = None) -> FlowResult:
        """Étape d'entrée utilisateur.

        Ici on laisse le core EnOcean gérer l’ajout via YAML ou par l’intégration core,
        notre custom n’ajoute pas de champs nouveaux au setup.
        """
        return self.async_abort(reason="use_core_setup")

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Retourne le gestionnaire d’options pour cette entrée de config.

        La signature DOIT accepter 'config_entry' (exigée par HA).
        """
        return EnOceanOptionsFlowHandler(config_entry)


class EnOceanOptionsFlowHandler(config_entries.OptionsFlow):
    """Gère le panneau d’options de l’intégration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Stocke l'entrée de configuration."""
        self._entry = config_entry

    async def async_step_init(self, user_input: Dict[str, Any] | None = None) -> FlowResult:
        """Première (et unique) étape des options.

        Pour l’instant, on ne propose pas d’options supplémentaires.
        On crée une entrée vide pour éviter les erreurs et sortir proprement.
        """
        # On pourrait exposer plus tard des options (ex: temps d’attente Base ID).
        return self.async_create_entry(title="", data=self._entry.options or {})
