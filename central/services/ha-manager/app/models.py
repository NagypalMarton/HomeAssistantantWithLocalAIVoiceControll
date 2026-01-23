"""
Database models for HA Manager
"""

from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

Base = declarative_base()

class HAInstance(Base):
    """Home Assistant instance model"""
    __tablename__ = "ha_instances"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    container_id = Column(String(255), nullable=True, index=True)
    container_name = Column(String(255), nullable=False, unique=True)
    status = Column(String(50), nullable=False, default="stopped")  # started, stopped, error
    host_port = Column(Integer, nullable=False, unique=True)
    docker_network = Column(String(255), nullable=False)
    timezone = Column(String(50), nullable=False, default="Europe/Budapest")
    
    # Access token for internal API communication
    internal_api_token = Column(String(255), nullable=True)
    
    # Configuration
    config_yaml = Column(Text, nullable=True)  # Full HA configuration
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True
