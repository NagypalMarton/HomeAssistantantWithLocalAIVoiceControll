"""
MicroPi Central Backend - User API Service
Main FastAPI application entry point
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import structlog

# Import routes
from app.routes import intent, auth, health, metrics
from app.middleware import RequestIDMiddleware, LoggingMiddleware
from app.prometheus_metrics import PrometheusMiddleware
from app.database import init_db, engine
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

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown"""
    # Startup
    logger.info("Starting MicroPi Central Backend...")
    try:
        await init_db(engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    try:
        await engine.dispose()
        logger.info("Application stopped")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))

# Create FastAPI app
app = FastAPI(
    title="MicroPi Central Backend",
    description="Voice control intent processing and execution service",
    version="1.0.0",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(PrometheusMiddleware)
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
app.include_router(metrics.router, prefix="/api/v1", tags=["monitoring"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(intent.router, prefix="/api/v1", tags=["intent"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.central_port,
        log_level="info",
    )
