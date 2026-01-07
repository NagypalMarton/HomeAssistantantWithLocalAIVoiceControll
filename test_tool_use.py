#!/usr/bin/env python3
"""Test Mikrobi tool-use capability."""
import asyncio
import aiohttp
import json

async def test_mikrobi():
    """Test tool execution."""
    # Prompt that should trigger tool use
    test_prompts = [
        "Turn on the bedroom light",
        "What is the temperature in the living room?",
        "Set the living room thermostat to 22 degrees",
    ]
    
    for prompt in test_prompts:
        print(f"\n{'='*60}")
        print(f"Testing prompt: {prompt}")
        print('='*60)
        
        # This would require Home Assistant API access with token
        # For now, we'll just show the structure
        print(f"Would send to Assist API:")
        print(f"  POST /api/conversation/process")
        print(f"  Text: {prompt}")
        print(f"  Expected: LLM generates JSON tool calls, executor runs them")

asyncio.run(test_mikrobi())
