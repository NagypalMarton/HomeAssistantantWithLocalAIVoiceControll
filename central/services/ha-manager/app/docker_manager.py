"""
Docker management service for HA instances
"""

import subprocess
import json
import structlog
from typing import Optional, Dict, Any
from app.config import settings
import uuid
from datetime import datetime

logger = structlog.get_logger()

class DockerManager:
    """Manages Docker containers for HA instances using CLI"""
    
    def __init__(self):
        try:
            # Test Docker connectivity
            result = subprocess.run(
                ["docker", "ps"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.available = True
                logger.info("Docker CLI initialized successfully")
            else:
                logger.warning("Docker CLI test failed, using mock mode", stderr=result.stderr)
                self.available = False
        except FileNotFoundError:
            logger.warning("Docker CLI not found, using mock mode for development")
            self.available = False
        except Exception as e:
            logger.warning("Failed to initialize Docker CLI, using mock mode", error=str(e))
            self.available = False
    
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
        try:
            logger.info(
                "creating_ha_instance",
                user_id=user_id,
                container_name=container_name,
                host_port=host_port,
            )
            
            if not self.available:
                # Development mode: return mock container info
                container_id = f"mock-{uuid.uuid4().hex[:12]}"
                logger.info(
                    "ha_instance_created_mock",
                    user_id=user_id,
                    container_id=container_id,
                    note="Using mock mode (Docker CLI not available)",
                )
                return {
                    "container_id": container_id,
                    "container_name": container_name,
                    "status": "running",
                    "host_port": host_port,
                }
            
            # Create volume
            volume_name = f"ha-{user_id}"
            subprocess.run(
                ["docker", "volume", "create", volume_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Create container
            cmd = [
                "docker", "run", "-d",
                "--name", container_name,
                "-p", f"{host_port}:8123",
                "-e", f"TZ={settings.ha_timezone}",
                "-v", f"{volume_name}:/config",
                "--network", settings.ha_network,
                "--restart", "unless-stopped",
                "--memory", settings.ha_memory_limit,
                "--label", f"micropi.user_id={user_id}",
                "--label", "micropi.managed=true",
                settings.ha_image,
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to create container: {result.stderr}")
            
            container_id = result.stdout.strip()
            logger.info(
                "ha_instance_created",
                user_id=user_id,
                container_id=container_id,
            )
            
            return {
                "container_id": container_id,
                "container_name": container_name,
                "status": "running",
                "host_port": host_port,
            }
        except subprocess.TimeoutExpired as e:
            logger.error("Docker command timeout", user_id=user_id, error=str(e))
            raise RuntimeError(f"Docker command timed out: {str(e)}")
        except Exception as e:
            logger.error("docker_create_error", error=str(e), user_id=user_id)
            raise
    
    async def start_ha_instance(self, container_id: str) -> bool:
        """
        Start a Home Assistant container
        
        Args:
            container_id: Docker container ID
            
        Returns:
            True if successful
        """
        try:
            if not self.available:
                # Mock mode
                logger.info("start_ha_instance_mock", container_id=container_id)
                return True
            
            result = subprocess.run(
                ["docker", "start", container_id],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to start container: {result.stderr}")
            
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
        try:
            if not self.available:
                # Mock mode
                logger.info("stop_ha_instance_mock", container_id=container_id)
                return True
            
            result = subprocess.run(
                ["docker", "stop", "-t", "10", container_id],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to stop container: {result.stderr}")
            
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
        try:
            if not self.available:
                # Mock mode
                logger.info("delete_ha_instance_mock", container_id=container_id, user_id=user_id)
                return True
            
            # Stop container
            subprocess.run(
                ["docker", "stop", "-t", "10", container_id],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            # Remove container
            subprocess.run(
                ["docker", "rm", container_id],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Remove volume
            volume_name = f"ha-{user_id}"
            subprocess.run(
                ["docker", "volume", "rm", volume_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
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
        try:
            if not self.available:
                # Development mode: return mock status
                logger.info("get_container_status_mock", container_id=container_id, note="Using mock mode")
                return {
                    "container_id": container_id,
                    "status": "running",
                    "state": {
                        "Running": True,
                        "Status": "running",
                        "StartedAt": datetime.now().isoformat(),
                    },
                }
            
            result = subprocess.run(
                ["docker", "inspect", container_id, "--format=json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to get container status: {result.stderr}")
            
            container_data = json.loads(result.stdout)
            if not container_data:
                raise RuntimeError(f"Container not found: {container_id}")
            
            state = container_data[0].get("State", {})
            return {
                "container_id": container_id,
                "status": "running" if state.get("Running") else state.get("Status", "unknown"),
                "state": state,
            }
        except json.JSONDecodeError as e:
            logger.error("Failed to parse Docker JSON", error=str(e))
            raise
        except Exception as e:
            logger.error("Failed to get container status", container_id=container_id, error=str(e))
            raise

# Singleton instance
docker_manager = DockerManager()
