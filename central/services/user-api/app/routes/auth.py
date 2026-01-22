"""
Authentication endpoints
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, validator
import structlog
import uuid
from typing import Optional
from app.constants import (
    VALIDATION_PASSWORD_MIN_LENGTH,
    TokenType,
    TEXT_MAX_LENGTH,
)
from app.exceptions import AuthenticationError, ValidationError
from app.security import (
    create_access_token,
    create_refresh_token,
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
async def login(request: LoginRequest):
    """User login - returns JWT tokens"""
    logger.info("login_attempt", email=request.email)
    # Minimal acceptance: generate tokens without DB for out-of-the-box demo
    user_id = str(uuid.uuid4())
    payload = {"sub": request.email, "uid": user_id}
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type=TokenType.BEARER.value,
    )

@router.post("/register", response_model=RegisterResponse)
async def register(request: RegisterRequest):
    """User registration"""
    logger.info("registration_attempt", email=request.email)
    # Minimal acceptance: echo back user id without DB persistence
    user_id = str(uuid.uuid4())
    return RegisterResponse(user_id=user_id, email=request.email)

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")

@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest) -> LoginResponse:
    """Refresh access token"""
    logger.info("refresh_token_attempt")
    payload = verify_token(request.refresh_token, token_type="refresh")
    user_id = payload.get("uid") or payload.get("sub")
    if not user_id:
        raise AuthenticationError("Refresh token missing user id")
    new_access = create_access_token({"sub": payload.get("sub"), "uid": user_id})
    new_refresh = create_refresh_token({"sub": payload.get("sub"), "uid": user_id})
    return LoginResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type=TokenType.BEARER.value,
    )
