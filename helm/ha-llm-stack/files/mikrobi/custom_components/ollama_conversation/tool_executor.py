"""Tool execution engine for Mikrobi agent."""
import json
import logging
from typing import Any

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class ToolExecutor:
    """Executes tools/services in Home Assistant."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize tool executor."""
        self.hass = hass

    def get_entities(self) -> list[dict]:
        """Get list of available entities with their states."""
        entities = []
        for state in self.hass.states.async_all():
            entities.append({
                "entity_id": state.entity_id,
                "state": state.state,
                "attributes": dict(state.attributes)
            })
        return entities

    async def execute_tool(self, tool_name: str, **kwargs) -> dict[str, Any]:
        """Execute a tool and return result."""
        _LOGGER.debug(f"Executing tool: {tool_name} with args: {kwargs}")

        try:
            if tool_name == "get_state":
                return await self._get_state(**kwargs)
            elif tool_name == "turn_on":
                return await self._turn_on(**kwargs)
            elif tool_name == "turn_off":
                return await self._turn_off(**kwargs)
            elif tool_name == "set_temperature":
                return await self._set_temperature(**kwargs)
            elif tool_name == "call_service":
                return await self._call_service(**kwargs)
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            _LOGGER.error(f"Tool execution error: {e}")
            return {"success": False, "error": str(e)}

    async def _get_state(self, entity_id: str, **_kwargs) -> dict[str, Any]:
        """Get state of an entity."""
        state = self.hass.states.get(entity_id)
        if state is None:
            return {"success": False, "error": f"Entity not found: {entity_id}"}
        
        return {
            "success": True,
            "entity_id": entity_id,
            "state": state.state,
            "attributes": dict(state.attributes)
        }

    async def _turn_on(self, entity_id: str, brightness: int = None, color_temp: int = None, **_kwargs) -> dict[str, Any]:
        """Turn on a light or switch."""
        domain = entity_id.split(".")[0]
        
        service_data = {"entity_id": entity_id}
        if brightness is not None:
            service_data["brightness"] = brightness
        if color_temp is not None:
            service_data["color_temp"] = color_temp

        try:
            await self.hass.services.async_call(domain, "turn_on", service_data)
            return {"success": True, "message": f"Turned on {entity_id}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _turn_off(self, entity_id: str, **_kwargs) -> dict[str, Any]:
        """Turn off a light or switch."""
        domain = entity_id.split(".")[0]
        
        try:
            await self.hass.services.async_call(domain, "turn_off", {"entity_id": entity_id})
            return {"success": True, "message": f"Turned off {entity_id}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _set_temperature(self, entity_id: str, temperature: float, **_kwargs) -> dict[str, Any]:
        """Set target temperature."""
        try:
            await self.hass.services.async_call(
                "climate",
                "set_temperature",
                {"entity_id": entity_id, "temperature": temperature}
            )
            return {"success": True, "message": f"Set {entity_id} temperature to {temperature}°C"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _call_service(self, domain: str, service: str, entity_id: str = None, data: dict = None, **_kwargs) -> dict[str, Any]:
        """Call a generic Home Assistant service."""
        service_data = data or {}
        if entity_id:
            service_data["entity_id"] = entity_id

        try:
            await self.hass.services.async_call(domain, service, service_data)
            return {"success": True, "message": f"Called {domain}.{service}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
