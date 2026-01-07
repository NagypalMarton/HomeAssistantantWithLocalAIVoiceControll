"""Ollama conversation agent."""
import logging
import aiohttp
import async_timeout

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.util import ulid

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


class OllamaConversationAgent(conversation.AbstractConversationAgent):
    """Ollama conversation agent."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        self.hass = hass
        self.entry = entry

    @property
    def attribution(self):
        """Return the attribution."""
        return {"name": "Powered by Ollama", "url": "https://ollama.ai"}

    @property
    def supported_languages(self) -> list[str] | str:
        """Return a list of supported languages."""
        return MATCH_ALL

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process a sentence."""
        from datetime import datetime, timedelta

        host = self.entry.data[CONF_HOST]
        model = self.entry.data.get("model", "ministral-3:3b-instruct-2512-q4_K_M")
        current_date = datetime.utcnow().strftime("%Y-%m-%d")
        yesterday_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        _LOGGER.debug("Processing: %s", user_input.text)

        try:
            async with aiohttp.ClientSession() as session:
                async with async_timeout.timeout(60):
                    async with session.post(
                        f"{host}/api/generate",
                        json={
                            "model": model,
                            "prompt": (
                                f"[SYSTEM_PROMPT]You are Ministral-3-3B-Instruct-2512, a Large Language Model (LLM) by Mistral AI. "
                                f"The current date is {current_date}. Yesterday's date is {yesterday_date}. "
                                f"Respond in the user's language. You cannot browse the web. Use tools if available; if not, explain you cannot perform the action.[/SYSTEM_PROMPT]\n"
                                f"[INST]{user_input.text}[/INST]"
                            ),
                            "stream": False,
                            "temperature": 0.4,
                            "num_predict": 150,
                        },
                    ) as response:
                        if response.status != 200:
                            _LOGGER.error("Ollama API error: %s", response.status)
                            response_text = "Sajnálom, hiba történt az Ollama kapcsolódás során."
                        else:
                            result = await response.json()
                            response_text = result.get("response", "Nem kaptam választ.").strip()
                            _LOGGER.debug("Ollama response: %s", response_text)

        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("Error calling Ollama: %s", err)
            response_text = f"Hiba: {str(err)}"

        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(response_text)
        
        return conversation.ConversationResult(
            conversation_id=user_input.conversation_id or ulid.ulid(),
            response=intent_response,
        )
