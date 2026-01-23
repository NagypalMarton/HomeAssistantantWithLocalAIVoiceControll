"""
HA Manager Configuration
"""

from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Server
    central_port: int = 8001
    central_env: str = "development"
    central_log_level: str = "INFO"
    
    # Database
    database_url: str = "postgresql://central_user:central_pass@localhost:5432/central_db"
    database_pool_size: int = 10
    database_echo: bool = False
    
    # Docker
    docker_host: str = "unix:///var/run/docker.sock"
    ha_image: str = "homeassistant/home-assistant:latest"
    ha_network: str = "central"
    ha_base_port: int = 8123
    ha_port_range_start: int = 8200
    ha_port_range_end: int = 8300
    
    # Home Assistant defaults
    ha_timezone: str = "Europe/Budapest"
    ha_latitude: float = 47.5
    ha_longitude: float = 19.04
    ha_elevation: int = 0
    ha_unit_system: str = "metric"
    ha_currency: str = "HUF"
    
    # Container resources
    ha_memory_limit: str = "512m"
    ha_cpu_limit: str = "0.5"
    
    # Security
    cors_allowed_origins: List[str] = ["http://localhost:8000"]
    debug_mode: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
