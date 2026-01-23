"""
Home Assistant instance management endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import HAInstance
from app.docker_manager import docker_manager
from app.config import settings

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
async def create_ha_instance(request: HAInstanceRequest):
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
        # Find an available port
        used_ports = set()  # TODO: Query from database
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
        
        # Create Docker container
        docker_result = await docker_manager.create_ha_instance(
            user_id=user_id,
            container_name=container_name,
            host_port=host_port,
        )
        
        # Start container
        await docker_manager.start_ha_instance(docker_result["container_id"])
        
        # TODO: Save to database
        
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
async def get_ha_instance(user_id: UUID):
    """
    Get Home Assistant instance details for a user
    
    Args:
        user_id: User UUID
        
    Returns:
        HAInstanceResponse with instance details
    """
    try:
        # TODO: Query from database
        
        logger.info("ha_instance_retrieved", user_id=str(user_id))
        
        return HAInstanceResponse(
            user_id=user_id,
            container_id="mock-container-id",
            container_name=f"ha-user-{str(user_id)[:8]}",
            status="running",
            host_port=8200,
        )
        
    except Exception as e:
        logger.error("Failed to get HA instance", user_id=str(user_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve HA instance"
        )

@router.delete("/ha/instance/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ha_instance(user_id: UUID):
    """
    Delete Home Assistant instance for a user
    
    Args:
        user_id: User UUID
    """
    try:
        # TODO: Query from database and delete
        
        logger.info("ha_instance_deleted", user_id=str(user_id))
        
    except Exception as e:
        logger.error("Failed to delete HA instance", user_id=str(user_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete HA instance"
        )

@router.get("/ha/instance/{user_id}/status")
async def get_ha_instance_status(user_id: UUID):
    """
    Get real-time status of a HA instance
    
    Args:
        user_id: User UUID
        
    Returns:
        Status information
    """
    try:
        # TODO: Query container status from Docker
        
        return {
            "user_id": str(user_id),
            "status": "running",
            "health": "healthy",
            "uptime_seconds": 3600,
        }
        
    except Exception as e:
        logger.error("Failed to get HA instance status", user_id=str(user_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get instance status"
        )
