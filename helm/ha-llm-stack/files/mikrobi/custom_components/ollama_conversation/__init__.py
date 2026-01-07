"""The Ollama Conversation integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ollama_conversation"

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Ollama Conversation component."""
    hass.data.setdefault(DOMAIN, {})
    
    # Auto-create config entry if none exists
    if not hass.config_entries.async_entries(DOMAIN):
        _LOGGER.info("Auto-creating Ollama Conversation integration")
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": "import"},
                data={
                    CONF_HOST: "http://ollama:11434",
                    "model": "ministral-3:3b-instruct-2512-q4_K_M",
                },
            )
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ollama Conversation from a config entry."""
    from homeassistant.components import conversation
    from .conversation import OllamaConversationAgent
    
    hass.data[DOMAIN][entry.entry_id] = entry.data
    
    # Create and register the conversation agent
    agent = OllamaConversationAgent(hass, entry)
    conversation.async_set_agent(hass, entry, agent)
    
    _LOGGER.info("Ollama Conversation agent registered successfully")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    from homeassistant.components import conversation
    
    conversation.async_unset_agent(hass, entry)
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
