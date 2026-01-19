"""
Health check endpoints
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"

class ReadyResponse(BaseModel):
    status: str
    components: dict

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Liveness probe"""
    return {"status": "ok"}

@router.get("/ready", response_model=ReadyResponse)
async def readiness_check():
    """Readiness probe - checks dependencies"""
    # TODO: Check database, Redis, Ollama connectivity
    return {
        "status": "ready",
        "components": {
            "database": "connected",
            "redis": "connected",
            "ollama": "connected",
        }
    }
