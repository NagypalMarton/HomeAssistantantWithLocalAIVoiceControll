"""
Authentication endpoints
"""

from datetime import datetime, timedelta
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field, validator
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.constants import (
    VALIDATION_PASSWORD_MIN_LENGTH,
    TokenType,
    TEXT_MAX_LENGTH,
)
from app.database import get_db
from app.exceptions import AuthenticationError, ValidationError
from app.models import User, RefreshToken
from app.redis_client import blacklist_token, is_token_blacklisted
from app.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)

router = APIRouter()
logger = structlog.get_logger()

class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = TokenType.BEARER.value

class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=TEXT_MAX_LENGTH, description="User password")
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError(VALIDATION_PASSWORD_MIN_LENGTH)
        return v

class RegisterResponse(BaseModel):
    user_id: str
    email: str
    message: str = "User registered successfully"

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """User login - returns JWT tokens"""
    logger.info("login_attempt", email=request.email)
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(request.password, user.password_hash):
        raise AuthenticationError("Invalid email or password")

    access_payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
    }
    access_token = create_access_token(access_payload)

    refresh_jti = str(uuid.uuid4())
    refresh_payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "jti": refresh_jti,
    }
    refresh_token = create_refresh_token(refresh_payload)
    refresh_expires = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)

    db.add(
        RefreshToken(
            user_id=user.id,
            token_jti=refresh_jti,
            expires_at=refresh_expires,
        )
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type=TokenType.BEARER.value,
    )

@router.post("/register", response_model=RegisterResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """User registration"""
    logger.info("registration_attempt", email=request.email)
    result = await db.execute(select(User).where(User.email == request.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise ValidationError("Email already registered")

    try:
        password_hash = hash_password(request.password)
    except ValueError as e:
        logger.error(
            "password_hash_failed",
            length=len(request.password),
            error=str(e),
        )
        raise ValidationError("Invalid password format")

    user = User(
        email=request.email,
        password_hash=password_hash,
    )
    db.add(user)
    await db.flush()

    return RegisterResponse(user_id=str(user.id), email=user.email)

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")

@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)) -> LoginResponse:
    """Refresh access token"""
    logger.info("refresh_token_attempt")
    payload = verify_token(request.refresh_token, token_type="refresh")
    user_id = payload.get("sub")
    token_jti = payload.get("jti")
    if not user_id or not token_jti:
        raise AuthenticationError("Refresh token missing user id or token id")

    if await is_token_blacklisted(token_jti):
        raise AuthenticationError("Refresh token revoked")

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == uuid.UUID(user_id),
            RefreshToken.token_jti == token_jti,
            RefreshToken.revoked_at.is_(None),
        )
    )
    stored = result.scalar_one_or_none()
    if not stored or stored.expires_at < datetime.utcnow():
        raise AuthenticationError("Refresh token expired or invalid")

    stored.revoked_at = datetime.utcnow()
    await blacklist_token(token_jti, stored.expires_at)

    new_access = create_access_token(
        {
            "sub": user_id,
            "email": payload.get("email"),
            "role": payload.get("role"),
        }
    )

    new_jti = str(uuid.uuid4())
    new_refresh = create_refresh_token(
        {
            "sub": user_id,
            "email": payload.get("email"),
            "role": payload.get("role"),
            "jti": new_jti,
        }
    )
    new_expires = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
    db.add(
        RefreshToken(
            user_id=uuid.UUID(user_id),
            token_jti=new_jti,
            expires_at=new_expires,
        )
    )

    return LoginResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type=TokenType.BEARER.value,
    )


@router.post("/logout")
async def logout(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Logout and revoke refresh token"""
    logger.info("logout_attempt")
    payload = verify_token(request.refresh_token, token_type="refresh")
    user_id = payload.get("sub")
    token_jti = payload.get("jti")
    if not user_id or not token_jti:
        raise AuthenticationError("Refresh token missing user id or token id")

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == uuid.UUID(user_id),
            RefreshToken.token_jti == token_jti,
            RefreshToken.revoked_at.is_(None),
        )
    )
    stored = result.scalar_one_or_none()
    if stored:
        stored.revoked_at = datetime.utcnow()
        await blacklist_token(token_jti, stored.expires_at)

    return {"status": "logged_out"}
