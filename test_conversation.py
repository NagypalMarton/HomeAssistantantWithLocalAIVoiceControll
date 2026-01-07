#!/usr/bin/env python3
"""Test conversation endpoint."""
import asyncio
import aiohttp
import json

async def test():
    """Test the Ollama conversation."""
    url = "http://localhost:8123/api/conversation/process"
    
    payload = {
        "text": "Szia!",
        "conversation_id": "test-conv-1"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkYjc3OWI0YmVkYjE0YTI0OTkwNjY0YTdjOTU0ZGQ3YiIsImlhdCI6MTczMDA1NjM1NiwiZXhwIjoyMDQ1NDE2MzU2fQ.gBVdEpn8tXw3b3gGp0fP_RXb2w8YKfJLcmUsmYlzZGg"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                print(f"Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    print(f"Response: {json.dumps(data, indent=2)}")
                else:
                    text = await resp.text()
                    print(f"Error: {text}")
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test())
