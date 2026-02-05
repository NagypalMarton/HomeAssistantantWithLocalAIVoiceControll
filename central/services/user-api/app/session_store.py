"""
Session context storage in Redis
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

from app.config import settings

SESSION_PREFIX = "session_context:"


def _build_session_key(user_id: str, session_id: Optional[str]) -> str:
    if session_id:
        return f"{SESSION_PREFIX}{user_id}:{session_id}"
    return f"{SESSION_PREFIX}{user_id}"


async def get_session_context(
    client: redis.Redis,
    user_id: str,
    session_id: Optional[str],
) -> List[Dict[str, Any]]:
    """Load session context for a user/session"""
    key = _build_session_key(user_id, session_id)
    raw = await client.get(key)
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if isinstance(data, list):
        return data
    return []


async def append_session_context(
    client: redis.Redis,
    user_id: str,
    session_id: Optional[str],
    entry: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Append an entry and trim to configured context window"""
    key = _build_session_key(user_id, session_id)
    context = await get_session_context(client, user_id, session_id)
    context.append(entry)
    trimmed = context[-settings.llm_context_window :]
    await client.set(key, json.dumps(trimmed), ex=settings.session_ttl_seconds)
    return trimmed


def build_context_entry(role: str, content: str) -> Dict[str, Any]:
    """Build a standardized context entry"""
    return {
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat(),
    }
