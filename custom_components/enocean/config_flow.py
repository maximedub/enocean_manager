# -*- coding: utf-8 -*-
"""
config_flow.py — Flux de configuration pour l'intégration custom EnOcean.

Objectifs :
- Supporter l'ajout manuel via l'UI (step 'user').
- Supporter l'import YAML (step 'import'), déclenché par __init__.py quand 'enocean:' est présent dans la config.
- Garantir une seule instance (single_instance_allowed).
- Valider le chemin du dongle si possible, sans bloquer l'import (les liens /dev peuvent apparaître plus tard).

On réutilise les helpers de dongle.py :
- detect() : suggestion de ports trouvés
- validate_path(path) : vérification d'accès au port série
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
    """Flux de configuration EnOcean."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Step affiché dans l'UI : saisie du port série."""
        errors: dict[str, str] = {}

        # Si l'utilisateur a soumis le formulaire
        if user_input is not None:
            device: str = user_input[CONF_DEVICE]

            # Valide le chemin (par l'executor, car appel bloquant)
            is_ok = await self.hass.async_add_executor_job(validate_path, device)
            if not is_ok:
                errors["base"] = "invalid_dongle_path"
            else:
                # Une seule instance autorisée
                if self._async_current_entries():
                    return self.async_abort(reason="single_instance_allowed")
                # Crée l'entrée de config
                return self.async_create_entry(title="EnOcean", data={CONF_DEVICE: device})

        # Pré-remplit avec une détection éventuelle
        ports = detect() or []
        default_device = ports[0] if ports else ""
        schema = vol.Schema({vol.Required(CONF_DEVICE, default=default_device): cv.string})

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={"ports": "\n".join(ports) if ports else "Aucun trouvé"},
        )

    async def async_step_import(self, user_input: dict) -> FlowResult:
        """Step appelé lors de l'import YAML (SOURCE_IMPORT)."""
        # Récupère le chemin fourni via configuration.yaml / packages
        device: str | None = user_input.get(CONF_DEVICE)
        if not device:
            # Si rien n'est fourni, on retombe sur le formulaire user
            return await self.async_step_user({})

        # Essaye de valider le chemin — mais n'empêche pas l'import si ça échoue
        try:
            _ = await self.hass.async_add_executor_job(validate_path, device)
        except Exception:
            # On ignore toute erreur ici pour ne pas bloquer l'import
            pass

        # Si une entrée existe déjà :
        if self._async_current_entries():
            # Si c'est exactement le même port, on évite le doublon
            for entry in self._async_current_entries():
                if entry.data.get(CONF_DEVICE) == device:
                    return self.async_abort(reason="already_configured")
            # Sinon, on reste mono-instance (cohérent avec l’intégration core)
            return self.async_abort(reason="single_instance_allowed")

        # Crée l’entrée depuis l’import YAML
        return self.async_create_entry(title="EnOcean", data={CONF_DEVICE: device})

    @callback
    def async_get_options_flow(self, config_entry):
        """Retourne le flow d’options (aucune option ici)."""
        return EnOceanOptionsFlow(config_entry)


class EnOceanOptionsFlow(config_entries.OptionsFlow):
    """Flux d'options (placeholder, pas d’options pour l’instant)."""

    def __init__(self, config_entry):
        # Référence à l'entrée de config (utile si on ajoute des options plus tard)
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Aucune option à configurer : on valide directement."""
        return self.async_create_entry(title="", data={})
