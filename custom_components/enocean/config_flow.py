"""Config flow pour l'intégration EnOcean custom.

- Supporte l'import YAML (step 'import')
- Fournit un OptionsFlow
- Expose la fonction module-level `async_get_options_flow` attendue par HA
"""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

# ----- Schémas -----
OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional("serial_port", default="/dev/ttyUSB0"): str,
        vol.Optional("auto_teachin", default=True): bool,
    }
)


class EnOceanFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Flux d'installation."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Démarrage via l'UI (peut simplement créer une entrée par défaut)."""
        if user_input is None:
            # On crée une entrée minimale; les options seront éditées ensuite.
            return self.async_create_entry(title="EnOcean", data={})
        return self.async_create_entry(title="EnOcean", data=user_input)

    async def async_step_import(self, import_data: dict | None = None) -> FlowResult:
        """Support de l'import YAML -> flow step 'import'."""
        # On accepte l'import, on stocke les données telles quelles dans l'entrée.
        return self.async_create_entry(title="EnOcean (import YAML)", data=import_data or {})


class EnOceanOptionsFlow(config_entries.OptionsFlow):
    """Écran d'options pour l'intégration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Première étape (et unique) des options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Valeurs actuelles (options > data)
        cur = {
            "serial_port": self._entry.options.get(
                "serial_port", self._entry.data.get("serial_port", "/dev/ttyUSB0")
            ),
            "auto_teachin": self._entry.options.get(
                "auto_teachin", self._entry.data.get("auto_teachin", True)
            ),
        }
        return self.async_show_form(step_id="init", data_schema=OPTIONS_SCHEMA, description_placeholders=cur)


# ---- Cette fonction (niveau module) est celle appelée par HA ----
@callback
def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
    """Point d’entrée OptionsFlow attendu par Home Assistant."""
    return EnOceanOptionsFlow(config_entry)
