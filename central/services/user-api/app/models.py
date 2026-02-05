"""
Database models and schema
"""

from sqlalchemy import Column, String, DateTime, Text, JSON, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.constants import (
    EMAIL_MAX_LENGTH,
    PASSWORD_HASH_LENGTH,
    HA_INSTANCE_URL_LENGTH,
    DEVICE_ID_MAX_LENGTH,
    ROLE_MAX_LENGTH,
    STATUS_MAX_LENGTH,
    REQUEST_ID_LENGTH,
    TOKEN_JTI_LENGTH,
    UserRole,
)

Base = declarative_base()

class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(EMAIL_MAX_LENGTH), unique=True, nullable=False, index=True)
    password_hash = Column(String(PASSWORD_HASH_LENGTH), nullable=False)
    ha_instance_url = Column(String(HA_INSTANCE_URL_LENGTH), nullable=True)
    ha_token_encrypted = Column(Text, nullable=True)  # Encrypted HA token
    role = Column(String(ROLE_MAX_LENGTH), default=UserRole.USER.value)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class Session(Base):
    """User session model"""
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    device_id = Column(String(DEVICE_ID_MAX_LENGTH), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    context = Column(JSON, default={})  # Rolling window of previous messages
    
class AuditLog(Base):
    """Audit log model"""
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    device_id = Column(String(DEVICE_ID_MAX_LENGTH), nullable=True)
    input_text = Column(Text, nullable=False)
    intent = Column(JSON, nullable=False)
    ha_response = Column(JSON, nullable=True)
    status = Column(String(STATUS_MAX_LENGTH), nullable=False)
    latency_ms = Column(Integer, nullable=True)
    llm_tokens = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    request_id = Column(String(REQUEST_ID_LENGTH), unique=True, index=True)


class RefreshToken(Base):
    """Refresh token persistence model"""
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    token_jti = Column(String(TOKEN_JTI_LENGTH), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
