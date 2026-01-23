"""
Docker management service for HA instances
"""

import docker
import structlog
from typing import Optional, Dict, Any
from app.config import settings

logger = structlog.get_logger()

class DockerManager:
    """Manages Docker containers for HA instances"""
    
    def __init__(self):
        try:
            self.client = docker.DockerClient(base_url=settings.docker_host)
            self.client.ping()
            logger.info("Docker client initialized", docker_host=settings.docker_host)
        except Exception as e:
            logger.error("Failed to connect to Docker", error=str(e))
            self.client = None
    
    async def create_ha_instance(
        self,
        user_id: str,
        container_name: str,
        host_port: int,
    ) -> Dict[str, Any]:
        """
        Create a new Home Assistant container for a user
        
        Args:
            user_id: User UUID
            container_name: Docker container name
            host_port: Host port to bind
            
        Returns:
            Container info dictionary
        """
        if not self.client:
            raise RuntimeError("Docker client not initialized")
        
        try:
            logger.info(
                "creating_ha_instance",
                user_id=user_id,
                container_name=container_name,
                host_port=host_port,
            )
            
            # Create container
            container = self.client.containers.create(
                image=settings.ha_image,
                name=container_name,
                ports={8123: host_port},
                environment={
                    "TZ": settings.ha_timezone,
                },
                volumes={
                    f"ha-{user_id}": {"bind": "/config", "mode": "rw"}
                },
                network=settings.ha_network,
                restart_policy={"Name": "unless-stopped", "MaximumRetryCount": 0},
                healthcheck={
                    "Test": ["CMD", "curl", "-f", "http://localhost:8123/"],
                    "Interval": 30000000000,  # 30 seconds in nanoseconds
                    "Timeout": 5000000000,    # 5 seconds
                    "Retries": 3,
                    "StartPeriod": 60000000000,  # 60 seconds
                },
                labels={
                    "micropi.user_id": user_id,
                    "micropi.managed": "true",
                },
                mem_limit=settings.ha_memory_limit,
                cpu_quota=settings.ha_cpu_limit,
            )
            
            logger.info(
                "ha_instance_created",
                user_id=user_id,
                container_id=container.id,
            )
            
            return {
                "container_id": container.id,
                "container_name": container_name,
                "status": "created",
                "host_port": host_port,
            }
        except docker.errors.APIError as e:
            logger.error("Docker API error", error=str(e), user_id=user_id)
            raise RuntimeError(f"Failed to create container: {str(e)}")
    
    async def start_ha_instance(self, container_id: str) -> bool:
        """
        Start a Home Assistant container
        
        Args:
            container_id: Docker container ID
            
        Returns:
            True if successful
        """
        if not self.client:
            raise RuntimeError("Docker client not initialized")
        
        try:
            container = self.client.containers.get(container_id)
            container.start()
            logger.info("ha_instance_started", container_id=container_id)
            return True
        except Exception as e:
            logger.error("Failed to start container", container_id=container_id, error=str(e))
            raise
    
    async def stop_ha_instance(self, container_id: str) -> bool:
        """
        Stop a Home Assistant container
        
        Args:
            container_id: Docker container ID
            
        Returns:
            True if successful
        """
        if not self.client:
            raise RuntimeError("Docker client not initialized")
        
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=10)
            logger.info("ha_instance_stopped", container_id=container_id)
            return True
        except Exception as e:
            logger.error("Failed to stop container", container_id=container_id, error=str(e))
            raise
    
    async def delete_ha_instance(self, container_id: str, user_id: str) -> bool:
        """
        Delete a Home Assistant container and its volume
        
        Args:
            container_id: Docker container ID
            user_id: User UUID (for volume cleanup)
            
        Returns:
            True if successful
        """
        if not self.client:
            raise RuntimeError("Docker client not initialized")
        
        try:
            # Stop and remove container
            try:
                container = self.client.containers.get(container_id)
                container.stop(timeout=10)
                container.remove()
            except docker.errors.NotFound:
                pass
            
            # Remove volume
            volume_name = f"ha-{user_id}"
            try:
                volume = self.client.volumes.get(volume_name)
                volume.remove()
            except docker.errors.NotFound:
                pass
            
            logger.info("ha_instance_deleted", container_id=container_id, user_id=user_id)
            return True
        except Exception as e:
            logger.error("Failed to delete container", container_id=container_id, error=str(e))
            raise
    
    async def get_container_status(self, container_id: str) -> Dict[str, Any]:
        """
        Get current status of a container
        
        Args:
            container_id: Docker container ID
            
        Returns:
            Container status info
        """
        if not self.client:
            raise RuntimeError("Docker client not initialized")
        
        try:
            container = self.client.containers.get(container_id)
            return {
                "container_id": container.id,
                "status": container.status,
                "state": container.attrs.get("State", {}),
            }
        except Exception as e:
            logger.error("Failed to get container status", container_id=container_id, error=str(e))
            raise

# Singleton instance
docker_manager = DockerManager()
