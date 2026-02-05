"""
Home Assistant instance management endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import HAInstance
from app.docker_manager import docker_manager
from app.config import settings
from app.database import get_db

router = APIRouter()
logger = structlog.get_logger()

class HAInstanceRequest(BaseModel):
    user_id: UUID = Field(..., description="User UUID")

class HAInstanceResponse(BaseModel):
    user_id: UUID
    container_id: Optional[str]
    container_name: str
    status: str
    host_port: int
    timezone: str = settings.ha_timezone

@router.post("/ha/instance", response_model=HAInstanceResponse, status_code=status.HTTP_201_CREATED)
async def create_ha_instance(request: HAInstanceRequest, db: AsyncSession = Depends(get_db)):
    """
    Create a new Home Assistant instance for a user
    
    Args:
        request: Request with user_id
        
    Returns:
        HAInstanceResponse with instance details
    """
    user_id = str(request.user_id)
    container_name = f"ha-user-{user_id[:8]}"
    
    try:
        # Check if user already has an instance
        existing = await db.execute(select(HAInstance).where(HAInstance.user_id == request.user_id))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="HA instance already exists for user"
            )

        # Find an available port
        used_result = await db.execute(select(HAInstance.host_port))
        used_ports = {row[0] for row in used_result.all()}
        host_port = None
        for port in range(settings.ha_port_range_start, settings.ha_port_range_end):
            if port not in used_ports:
                host_port = port
                break
        
        if not host_port:
            raise HTTPException(
                status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
                detail="No available ports for new HA instance"
            )
        
        instance = HAInstance(
            user_id=request.user_id,
            container_name=container_name,
            status="creating",
            host_port=host_port,
            docker_network=settings.ha_network,
            timezone=settings.ha_timezone,
        )
        db.add(instance)
        await db.flush()

        # Create Docker container
        docker_result = await docker_manager.create_ha_instance(
            user_id=user_id,
            container_name=container_name,
            host_port=host_port,
        )
        
        # Start container
        await docker_manager.start_ha_instance(docker_result["container_id"])
        
        instance.container_id = docker_result["container_id"]
        instance.status = "running"
        
        logger.info(
            "ha_instance_created_successfully",
            user_id=user_id,
            container_id=docker_result["container_id"],
            host_port=host_port,
        )
        
        return HAInstanceResponse(
            user_id=request.user_id,
            container_id=docker_result["container_id"],
            container_name=container_name,
            status="running",
            host_port=host_port,
        )
        
    except Exception as e:
        logger.error("Failed to create HA instance", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create HA instance: {str(e)}"
        )

@router.get("/ha/instance/{user_id}", response_model=HAInstanceResponse)
async def get_ha_instance(user_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get Home Assistant instance details for a user
    
    Args:
        user_id: User UUID
        
    Returns:
        HAInstanceResponse with instance details
    """
    try:
        result = await db.execute(select(HAInstance).where(HAInstance.user_id == user_id))
        instance = result.scalar_one_or_none()
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="HA instance not found",
            )

        logger.info("ha_instance_retrieved", user_id=str(user_id))

        return HAInstanceResponse(
            user_id=user_id,
            container_id=instance.container_id,
            container_name=instance.container_name,
            status=instance.status,
            host_port=instance.host_port,
        )
        
    except Exception as e:
        logger.error("Failed to get HA instance", user_id=str(user_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve HA instance"
        )

@router.delete("/ha/instance/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ha_instance(user_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Delete Home Assistant instance for a user
    
    Args:
        user_id: User UUID
    """
    try:
        result = await db.execute(select(HAInstance).where(HAInstance.user_id == user_id))
        instance = result.scalar_one_or_none()
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="HA instance not found",
            )

        if instance.container_id:
            await docker_manager.delete_ha_instance(instance.container_id, str(user_id))

        await db.delete(instance)
        logger.info("ha_instance_deleted", user_id=str(user_id))
        
    except Exception as e:
        logger.error("Failed to delete HA instance", user_id=str(user_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete HA instance"
        )

@router.get("/ha/instance/{user_id}/status")
async def get_ha_instance_status(user_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get real-time status of a HA instance
    
    Args:
        user_id: User UUID
        
    Returns:
        Status information
    """
    try:
        result = await db.execute(select(HAInstance).where(HAInstance.user_id == user_id))
        instance = result.scalar_one_or_none()
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="HA instance not found",
            )

        if not instance.container_id:
            return {
                "user_id": str(user_id),
                "status": instance.status,
                "health": "unknown",
                "uptime_seconds": 0,
            }

        container_status = await docker_manager.get_container_status(instance.container_id)
        state = container_status.get("state", {})
        started_at = state.get("StartedAt")
        uptime_seconds = 0
        if started_at:
            try:
                if isinstance(started_at, str):
                    if started_at.endswith("Z"):
                        started_at = started_at.replace("Z", "+00:00")
                    uptime_seconds = int(
                        (datetime.now(timezone.utc) - datetime.fromisoformat(started_at)).total_seconds()
                    )
            except (ValueError, TypeError):
                uptime_seconds = 0

        return {
            "user_id": str(user_id),
            "status": container_status.get("status"),
            "health": state.get("Health", {}).get("Status", "unknown") if isinstance(state.get("Health"), dict) else "unknown",
            "uptime_seconds": uptime_seconds,
        }
        
    except Exception as e:
        logger.error("Failed to get HA instance status", user_id=str(user_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get instance status"
        )
