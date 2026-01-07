#!/usr/bin/env python3
"""Test Ollama with simple prompt."""
import asyncio
import aiohttp
import json

async def test():
    host = "http://ollama:11434"
    model = "ministral-3:3b-instruct-2512-q4_K_M"
    
    # Try with a very simple prompt
    payload = {
        "model": model,
        "prompt": "Hi",
        "stream": False,
        "temperature": 0.4,
        "num_predict": 10,
    }
    
    print("Testing with simple prompt...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with asyncio.timeout(60):
                async with session.post(
                    f"{host}/api/generate",
                    json=payload
                ) as resp:
                    print(f"Status: {resp.status}")
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"Success: {data['response']}")
                    else:
                        text = await resp.text()
                        print(f"Error: {text[:200]}")
    except Exception as e:
        print(f"Exception: {e}")

asyncio.run(test())
