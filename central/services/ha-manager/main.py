"""
MicroPi Central - HA Manager Service
Manages per-user Home Assistant instances via Docker
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import structlog

# Import routes
from app.routes import health, ha_instances
from app.middleware import RequestIDMiddleware, LoggingMiddleware
from app.database import init_db
from app.config import settings

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Database setup
DATABASE_URL = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.database_echo,
    pool_size=settings.database_pool_size,
)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown"""
    # Startup
    logger.info("Starting MicroPi HA Manager...")
    try:
        await init_db(engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down HA Manager...")
    try:
        await engine.dispose()
        logger.info("HA Manager stopped")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))

# Create FastAPI app
app = FastAPI(
    title="MicroPi HA Manager",
    description="Per-user Home Assistant instance management service",
    version="1.0.0",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(ha_instances.router, prefix="/api/v1", tags=["ha_instances"])

# Dependency for session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency: Get database session"""
    async with AsyncSessionLocal() as session:
        yield session
