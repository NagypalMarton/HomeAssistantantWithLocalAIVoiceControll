"""
Configuration management using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Server
    central_port: int = 8000
    central_env: str = "development"
    central_log_level: str = "INFO"
    
    # Database
    database_url: str = "postgresql://central_user:central_pass@localhost:5432/central_db"
    database_pool_size: int = 10
    database_echo: bool = False
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_pool_size: int = 20
    
    # JWT & Auth
    jwt_secret: str  # Required - must be set via environment variable
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7
    
    # LLM (Ollama)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral:7b"
    llm_timeout_seconds: int = 5
    llm_context_window: int = 10
    
    # Home Assistant
    ha_default_domain: str = "http://localhost:8123"
    ha_api_timeout_seconds: int = 5
    ha_retry_count: int = 3
    ha_retry_backoff_factor: float = 2.0
    
    # Audit & Security
    audit_retention_days: int = 90
    rate_limit_per_user_per_minute: int = 10
    rate_limit_global_per_second: int = 100
    cors_allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Feature Flags
    feature_llm_caching: bool = True
    feature_ha_fallback_mode: bool = True
    debug_mode: bool = False
    
    # Monitoring
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    zabbix_agent_enabled: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.jwt_secret or self.jwt_secret == "your-256-bit-secret-change-this":
            raise ValueError(
                "JWT_SECRET environment variable must be set to a secure random value. "
                "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )

settings = Settings()
