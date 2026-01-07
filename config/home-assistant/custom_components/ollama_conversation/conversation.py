"""Ollama conversation agent."""
import asyncio
import json
import logging
import re
import aiohttp

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.util import ulid

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

try:
    from .tools import TOOLS, format_tools_for_prompt, format_available_entities
    from .tool_executor import ToolExecutor
    TOOLS_AVAILABLE = True
except ImportError as e:
    _LOGGER.warning(f"Tool system not available: {e}")
    TOOLS_AVAILABLE = False


class OllamaConversationAgent(conversation.AbstractConversationAgent):
    """Ollama conversation agent."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        self.hass = hass
        self.entry = entry
        self._id = "mikrobi"
        self._name = "Mikrobi"
        self.executor = ToolExecutor(hass) if TOOLS_AVAILABLE else None

    @property
    def attribution(self):
        """Return the attribution."""
        return {"name": "Powered by Ollama", "url": "https://ollama.ai"}

    @property
    def id(self) -> str:
        """Return a stable ID for the agent."""
        return self._id

    @property
    def name(self) -> str:
        """Return the display name for the agent (Assist label)."""
        return self._name

    @property
    def supported_languages(self) -> list[str] | str:
        """Return a list of supported languages."""
        return MATCH_ALL

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process a sentence with optional tool use capability."""
        from datetime import datetime, timedelta

        host = self.entry.data[CONF_HOST]
        model = self.entry.data.get("model", "ministral-3:3b-instruct-2512-q4_K_M")
        current_date = datetime.utcnow().strftime("%Y-%m-%d")
        yesterday_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        _LOGGER.debug("Processing: %s", user_input.text)

        # Build prompt with optional tool context
        if TOOLS_AVAILABLE and self.executor:
            try:
                entities = self.executor.get_entities()
                entities_context = format_available_entities(entities)
                tools_context = format_tools_for_prompt()
                system_prompt = (
                    f"You are Mikrobi, a Home Assistant AI assistant.\n"
                    f"Date: {current_date}.\n\n"
                    f"{tools_context}"
                    f"{entities_context}"
                )
            except Exception as e:
                _LOGGER.warning(f"Tool context failed, falling back: {e}")
                TOOLS_AVAILABLE = False
                system_prompt = "You are Mikrobi, a Home Assistant AI assistant. Respond in the user's language."
        else:
            system_prompt = "You are Mikrobi, a Home Assistant AI assistant. Respond in the user's language."

        prompt = f"{system_prompt}[INST]{user_input.text}[/INST]"
        
        # Call Ollama
        response_text = await self._call_ollama(host, model, prompt)
        if response_text is None:
            response_text = "Sajnálom, hiba történt az Ollama kapcsolódás során."

        # Try to parse and execute tools if enabled
        if TOOLS_AVAILABLE and self.executor and response_text:
            try:
                tool_results = await self._parse_and_execute_tools(response_text)
                if tool_results:
                    # Get refinement from LLM
                    tool_results_str = json.dumps(tool_results, ensure_ascii=False)
                    refinement = (
                        f"User asked: {user_input.text}\n"
                        f"Tool results: {tool_results_str}\n"
                        f"Explain what happened."
                    )
                    refined = await self._call_ollama(host, model, refinement)
                    if refined:
                        response_text = refined
            except Exception as e:
                _LOGGER.debug(f"Tool execution failed, using original response: {e}")
                pass  # Use original response

        # Clean up any JSON artifacts from response
        response_text = re.sub(r'\[[\s\S]*?\]', '', response_text).strip()

        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(response_text)
        
        return conversation.ConversationResult(
            conversation_id=user_input.conversation_id or ulid.ulid(),
            response=intent_response,
        )

    async def _call_ollama(self, host: str, model: str, prompt: str) -> str | None:
        """Call Ollama API and return response text."""
        try:
            _LOGGER.debug(f"Calling Ollama at {host} with model {model}")
            async with aiohttp.ClientSession() as session:
                try:
                    async with asyncio.timeout(120):  # Increased timeout
                        payload = {
                            "model": model,
                            "prompt": prompt,
                            "stream": False,
                            "temperature": 0.4,
                            "num_predict": 150,  # Reduced from 300 to speed up generation
                        }
                        _LOGGER.debug(f"Sending payload: {payload}")
                        async with session.post(
                            f"{host}/api/generate",
                            json=payload,
                            headers={"Content-Type": "application/json"}
                        ) as response:
                            _LOGGER.debug(f"Ollama response status: {response.status}")
                            if response.status != 200:
                                error_text = await response.text()
                                _LOGGER.error(f"Ollama API error {response.status}: {error_text}")
                                return None
                            result = await response.json()
                            response_text = result.get("response", "").strip()
                            _LOGGER.debug(f"Ollama response text: {response_text[:100]}")
                            return response_text
                except asyncio.TimeoutError:
                    _LOGGER.error("Timeout calling Ollama API after 120 seconds")
                    return None
        except Exception as err:
            _LOGGER.error(f"Error calling Ollama: {err}", exc_info=True)
            return None

    async def _parse_and_execute_tools(self, response_text: str) -> list[dict]:
        """Parse JSON tool calls from LLM response and execute them."""
        tool_results = []

        # Extract JSON arrays from response
        json_pattern = r'\[[\s\S]*?\]'
        json_matches = re.findall(json_pattern, response_text)

        for json_str in json_matches:
            try:
                tools_data = json.loads(json_str)
                if not isinstance(tools_data, list):
                    tools_data = [tools_data]

                for tool_call in tools_data:
                    if not isinstance(tool_call, dict):
                        continue

                    tool_name = tool_call.get("tool")
                    if not tool_name:
                        continue

                    # Validate tool exists
                    if not any(t["name"] == tool_name for t in TOOLS):
                        _LOGGER.warning(f"Unknown tool requested: {tool_name}")
                        tool_results.append({
                            "tool": tool_name,
                            "success": False,
                            "error": f"Unknown tool: {tool_name}"
                        })
                        continue

                    # Execute tool
                    result = await self.executor.execute_tool(tool_name, **tool_call)
                    tool_results.append({"tool": tool_name, **result})
                    _LOGGER.debug(f"Tool result: {result}")

            except json.JSONDecodeError:
                _LOGGER.debug(f"Could not parse JSON from response: {json_str}")
                continue

        return tool_results
