"""
Intent processing endpoints - the core pipeline
"""

from fastapi import APIRouter, HTTPException, status, Header, Depends
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import time
import uuid
import structlog
from app.constants import (
    TEXT_MIN_LENGTH,
    TEXT_MAX_LENGTH,
    VALIDATION_TEXT_REQUIRED,
    VALIDATION_TEXT_TOO_LONG,
    VALIDATION_USER_ID_REQUIRED,
    VALIDATION_DEVICE_ID_REQUIRED,
    IntentStatus,
)
from app.exceptions import AuthenticationError, ValidationError

router = APIRouter()
logger = structlog.get_logger()

class IntentRequest(BaseModel):
    user_id: str = Field(..., description="User UUID")
    device_id: str = Field(..., description="Device identifier")
    text: str = Field(..., min_length=TEXT_MIN_LENGTH, max_length=TEXT_MAX_LENGTH, description="User input text")
    session_id: Optional[str] = Field(None, description="Optional session ID for context")
    timestamp: Optional[str] = Field(None, description="Optional timestamp")
    
    @validator('text')
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError(VALIDATION_TEXT_REQUIRED)
        if len(v) > TEXT_MAX_LENGTH:
            raise ValueError(VALIDATION_TEXT_TOO_LONG)
        return v.strip()

class IntentResponse(BaseModel):
    request_id: str
    intent: str
    entity_id: Optional[str] = None
    response: str
    status: str  # Use IntentStatus enum values
    latency_ms: int

class ErrorResponse(BaseModel):
    request_id: str
    status: str
    message: str
    error_code: str

@router.post("/intent", response_model=IntentResponse)
async def process_intent(request: IntentRequest, authorization: str = Header(None)):
    """
    Core intent processing endpoint
    
    Flow:
    1. Authenticate user (JWT)
    2. Load session context
    3. Call LLM service for intent recognition
    4. Execute intent on per-user HA instance
    5. Generate response
    6. Log to audit trail
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # 1. Authenticate
        if not authorization or not authorization.startswith("Bearer "):
            logger.warning("auth_failed", request_id=request_id, user_id=request.user_id)
            raise AuthenticationError("Missing or invalid authorization token")
        
        token: str = authorization.split(" ")[1]
        # TODO: Verify JWT token
        
        logger.info(
            "intent_received",
            request_id=request_id,
            user_id=request.user_id,
            device_id=request.device_id,
            text=request.text,
        )
        
        # 2. Load session context
        # TODO: Load from Redis/DB
        
        # 3. Call LLM service
        # TODO: Call Ollama to recognize intent
        llm_response = {
            "intent": "turn_on",
            "entity_id": "light.nappali",
            "parameters": {"brightness": 255}
        }
        
        # 4. Execute on HA
        # TODO: Call per-user HA instance
        ha_response = {
            "state": "on",
            "entity_id": "light.nappali"
        }
        
        # 5. Generate response text
        response_text = "Bekapcsoltam a nappali lámpát"
        
        # 6. Log to audit trail
        latency_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "intent_success",
            request_id=request_id,
            user_id=request.user_id,
            intent=llm_response.get("intent"),
            latency_ms=latency_ms,
        )
        
        # TODO: Persist audit log to DB
        
        return IntentResponse(
            request_id=request_id,
            intent=llm_response.get("intent", ""),
            entity_id=llm_response.get("entity_id"),
            response=response_text,
            status=IntentStatus.SUCCESS.value,
            latency_ms=latency_ms,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "intent_error",
            request_id=request_id,
            user_id=request.user_id,
            error=str(e),
            latency_ms=latency_ms,
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process intent"
        )

@router.post("/intent/batch")
async def process_intent_batch(requests: list[IntentRequest]):
    """Batch intent processing (optional)"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Batch processing not yet implemented"
    )
