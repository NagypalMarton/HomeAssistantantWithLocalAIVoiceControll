#!/usr/bin/env python3
"""Test Ollama conversation directly."""
import asyncio
import aiohttp
import json

async def test_ollama():
    """Test Ollama API call."""
    host = "http://ollama:11434"
    model = "ministral-3:3b-instruct-2512-q4_K_M"
    
    payload = {
        "model": model,
        "prompt": "Szia! Mondj nekem egy viccet!",
        "stream": False,
        "temperature": 0.4,
        "num_predict": 100,
    }
    
    print(f"Calling {host}/api/generate with model {model}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with asyncio.timeout(30):
                async with session.post(
                    f"{host}/api/generate",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    print(f"Status: {response.status}")
                    if response.status == 200:
                        result = await response.json()
                        print(f"Response: {result['response'][:200]}")
                    else:
                        text = await response.text()
                        print(f"Error: {text}")
    except asyncio.TimeoutError:
        print("Timeout!")
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ollama())
