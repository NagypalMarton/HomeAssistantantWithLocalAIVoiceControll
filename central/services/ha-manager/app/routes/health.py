"""
Health check endpoints
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import structlog

router = APIRouter()
logger = structlog.get_logger()

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="ha-manager",
        version="1.0.0",
    )

@router.get("/health/live")
async def liveness():
    """Kubernetes liveness probe"""
    return {"status": "alive"}

@router.get("/health/ready")
async def readiness():
    """Kubernetes readiness probe"""
    return {"status": "ready"}
