"""Config flow for Ollama Conversation integration."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ollama_conversation"

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="http://ollama:11434"): str,
        vol.Required("model", default="ministral-3:3b-instruct-2512-q4_K_M"): str,
    }
)


class OllamaConversationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ollama Conversation."""

    VERSION = 1

    async def async_step_import(self, import_data: dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_data)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        # Test connection to Ollama
        errors = {}
        try:
            # Basic validation
            if not user_input[CONF_HOST].startswith("http"):
                errors[CONF_HOST] = "invalid_url"
        except Exception:  # pylint: disable=broad-except
            errors["base"] = "unknown"

        if errors:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
            )

        # Check if already configured
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(title="Ollama", data=user_input)
