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
    """Format tools as a readable prompt section for the LLM."""
    tools_text = "AVAILABLE TOOLS:\n\n"
    for tool in TOOLS:
        tools_text += f"Tool: {tool['name']}\n"
        tools_text += f"Description: {tool['description']}\n"
        tools_text += f"Parameters:\n"
        props = tool["parameters"]["properties"]
        required = tool["parameters"].get("required", [])
        for param_name, param_schema in props.items():
            required_str = " (required)" if param_name in required else " (optional)"
            tools_text += f"  - {param_name}: {param_schema.get('type', 'string')}{required_str}\n"
            if "description" in param_schema:
                tools_text += f"    {param_schema['description']}\n"
        tools_text += "\n"
    return tools_text


def format_available_entities(entity_list: list[dict]) -> str:
    """Format available entities for the LLM context."""
    if not entity_list:
        return "No entities available."
    
    entities_by_domain = {}
    for entity in entity_list:
        domain = entity["entity_id"].split(".")[0]
        if domain not in entities_by_domain:
            entities_by_domain[domain] = []
        entities_by_domain[domain].append(entity)
    
    entities_text = "AVAILABLE ENTITIES:\n\n"
    for domain in sorted(entities_by_domain.keys()):
        entities_text += f"{domain.upper()}:\n"
        for entity in entities_by_domain[domain][:10]:  # Limit to 10 per domain to save tokens
            state = entity.get("state", "unknown")
            friendly_name = entity.get("attributes", {}).get("friendly_name", entity["entity_id"])
            entities_text += f"  - {entity['entity_id']} ({friendly_name}): {state}\n"
        if len(entities_by_domain[domain]) > 10:
            entities_text += f"  ... and {len(entities_by_domain[domain]) - 10} more\n"
        entities_text += "\n"
    return entities_text
