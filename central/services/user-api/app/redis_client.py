"""
Redis client utilities
"""

from datetime import datetime
from typing import Optional

import redis.asyncio as redis

from app.config import settings

_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Get or initialize the Redis client"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


async def get_redis() -> redis.Redis:
    """Dependency: Get Redis client"""
    return get_redis_client()


def build_blacklist_key(token_jti: str) -> str:
    """Build Redis key for token blacklist"""
    return f"token_blacklist:{token_jti}"


async def blacklist_token(token_jti: str, expires_at: datetime) -> None:
    """Add token JTI to Redis blacklist until its expiration"""
    ttl_seconds = int((expires_at - datetime.utcnow()).total_seconds())
    if ttl_seconds <= 0:
        return
    client = get_redis_client()
    await client.set(build_blacklist_key(token_jti), "1", ex=ttl_seconds)


async def is_token_blacklisted(token_jti: str) -> bool:
    """Check if token JTI is in Redis blacklist"""
    client = get_redis_client()
    value = await client.get(build_blacklist_key(token_jti))
    return value is not None
