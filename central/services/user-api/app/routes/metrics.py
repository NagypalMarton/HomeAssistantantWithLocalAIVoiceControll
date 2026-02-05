"""
Metrics endpoint for Prometheus
"""

from fastapi import APIRouter
from fastapi.responses import Response
from app.prometheus_metrics import get_metrics

router = APIRouter()


@router.get("/metrics", tags=["monitoring"])
async def metrics():
    """
    Prometheus metrics endpoint
    
    Returns metrics in Prometheus text format
    """
    return Response(
        content=get_metrics(),
        media_type="text/plain; version=0.0.4"
    )
