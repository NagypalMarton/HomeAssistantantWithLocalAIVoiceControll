"""
Database models and schema
"""

from sqlalchemy import Column, String, DateTime, Text, JSON, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

Base = declarative_base()

class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    ha_instance_url = Column(String(255), nullable=True)
    ha_token_encrypted = Column(Text, nullable=True)  # Encrypted HA token
    role = Column(String(20), default="user")  # 'user', 'admin'
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class Session(Base):
    """User session model"""
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    device_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    context = Column(JSON, default={})  # Rolling window of previous messages
    
class AuditLog(Base):
    """Audit log model"""
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    device_id = Column(String(255), nullable=True)
    input_text = Column(Text, nullable=False)
    intent = Column(JSON, nullable=False)
    ha_response = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False)  # 'success', 'error', 'timeout'
    latency_ms = Column(Integer, nullable=True)
    llm_tokens = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    request_id = Column(String(255), unique=True, index=True)
