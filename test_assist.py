#!/usr/bin/env python3
"""Simple test to trigger Assist conversation."""
import sys
import asyncio
import json

# Add HA config path
sys.path.insert(0, '/config')

async def test_conversation():
    """Test the Ollama conversation agent."""
    try:
        # Import HA and custom component
        from homeassistant.core import HomeAssistant
        from homeassistant.components.conversation import async_converse
        from homeassistant.config_entries import ConfigEntry
        
        # Create minimal HA instance
        hass = HomeAssistant()
        
        # Try to call the conversation
        response = await async_converse(
            hass,
            "Szia!",
            conversation_id="test-1"
        )
        
        print(f"Success: {response}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_conversation())
