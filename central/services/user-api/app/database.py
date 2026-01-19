"""
Database initialization and utilities
"""

from sqlalchemy.ext.asyncio import AsyncEngine
from app.models import Base

async def init_db(engine: AsyncEngine) -> None:
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
