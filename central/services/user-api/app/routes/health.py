"""
Health check endpoints
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict
from app.constants import ComponentStatus

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"

class ReadyResponse(BaseModel):
    status: str
    components: Dict[str, str]

@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Liveness probe"""
    return HealthResponse(status="ok")

@router.get("/ready", response_model=ReadyResponse)
async def readiness_check() -> ReadyResponse:
    """Readiness probe - checks dependencies"""
    # TODO: Check database, Redis, Ollama connectivity
    return ReadyResponse(
        status="ready",
        components={
            "database": ComponentStatus.CONNECTED.value,
            "redis": ComponentStatus.CONNECTED.value,
            "ollama": ComponentStatus.CONNECTED.value,
        }
    )
