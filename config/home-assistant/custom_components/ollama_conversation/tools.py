"""Tool definitions for Mikrobi agent to interact with Home Assistant."""

TOOLS = [
    {
        "name": "get_state",
        "description": "Get the current state of a Home Assistant entity. Returns the entity's state and attributes.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The entity ID (e.g., 'light.bedroom', 'sensor.temperature', 'climate.living_room')"
                }
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "turn_on",
        "description": "Turn on a light, switch, or other entity. For lights, you can set brightness (0-255) and color.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The entity ID of the light or switch (e.g., 'light.bedroom', 'switch.fan')"
                },
                "brightness": {
                    "type": "integer",
                    "description": "Brightness level for lights (0-255, where 255 is full brightness). Optional.",
                    "minimum": 0,
                    "maximum": 255
                },
                "color_temp": {
                    "type": "integer",
                    "description": "Color temperature in Kelvin (e.g., 2700 for warm, 6500 for cold). Optional."
                }
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "turn_off",
        "description": "Turn off a light, switch, or other entity.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The entity ID of the light or switch (e.g., 'light.bedroom', 'switch.fan')"
                }
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "set_temperature",
        "description": "Set the target temperature for a climate entity (thermostat).",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The entity ID of the climate entity (e.g., 'climate.living_room')"
                },
                "temperature": {
                    "type": "number",
                    "description": "Target temperature in degrees Celsius"
                }
            },
            "required": ["entity_id", "temperature"]
        }
    },
    {
        "name": "call_service",
        "description": "Call any Home Assistant service. Use this for advanced actions not covered by other tools.",
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "The service domain (e.g., 'homeassistant', 'light', 'switch', 'climate')"
                },
                "service": {
                    "type": "string",
                    "description": "The service name (e.g., 'turn_on', 'turn_off', 'toggle')"
                },
                "entity_id": {
                    "type": "string",
                    "description": "The entity ID to target. Optional for some services."
                },
                "data": {
                    "type": "object",
                    "description": "Additional service data as key-value pairs. Optional."
                }
            },
            "required": ["domain", "service"]
        }
    }
]


def format_tools_for_prompt() -> str:
    """Format tools as a concise prompt section for the LLM."""
    tools_text = "TOOLS: You can use these tools by outputting JSON:\n"
    for tool in TOOLS:
        tools_text += f"- {tool['name']}: {tool['description']}\n"
    tools_text += "\nOutput tool calls as JSON arrays like: [{\"tool\":\"turn_on\",\"entity_id\":\"light.bedroom\"}]\n\n"
    return tools_text


def format_available_entities(entity_list: list[dict]) -> str:
    """Format available entities concisely for the LLM context."""
    if not entity_list:
        return "ENTITIES: None available.\n"
    
    # Only include first 15 entities total to keep prompt short
    entity_list = entity_list[:15]
    
    entities_text = "ENTITIES: "
    entity_strs = []
    for entity in entity_list:
        state = entity.get("state", "?")
        friendly_name = entity.get("attributes", {}).get("friendly_name", entity["entity_id"].split(".")[-1])
        entity_strs.append(f"{entity['entity_id']}={state}")
    
    entities_text += ", ".join(entity_strs) + "\n\n"
    return entities_text
