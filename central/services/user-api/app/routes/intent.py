"""
Intent processing endpoints - the core pipeline
"""

from fastapi import APIRouter, HTTPException, status, Header, Depends
from pydantic import BaseModel, Field, validator
from typing import Optional, AsyncGenerator
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
from app.exceptions import AuthenticationError, ValidationError, LLMError
from app.llm_service import ollama_service
from app.security import get_user_id_from_token
from sqlalchemy.ext.asyncio import AsyncSession

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
    confidence: Optional[float] = None

class ErrorResponse(BaseModel):
    request_id: str
    status: str
    message: str
    error_code: str

@router.post("/intent", response_model=IntentResponse)
async def process_intent(
    request: IntentRequest,
    authorization: str = Header(None),
):
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
        try:
            user_id = get_user_id_from_token(token)
        except Exception as e:
            logger.warning("token_validation_failed", request_id=request_id, error=str(e))
            raise AuthenticationError("Invalid token")
        
        logger.info(
            "intent_received",
            request_id=request_id,
            user_id=request.user_id,
            device_id=request.device_id,
            text=request.text[:50],
        )
        
        # 2. Load session context
        # TODO: Load from Redis/DB based on session_id or user_id
        session_context = None
        
        # 3. Call LLM service to recognize intent
        try:
            intent_data = await ollama_service.process_intent(
                user_text=request.text,
                ha_context=None,  # TODO: Load from user's HA instance
                session_context=session_context,
            )
        except LLMError as e:
            logger.error("llm_processing_failed", request_id=request_id, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LLM service unavailable"
            )
        
        # Check confidence threshold
        confidence = intent_data.get("confidence", 0.0)
        if confidence < 0.5:
            logger.warning(
                "low_confidence_intent",
                request_id=request_id,
                intent=intent_data.get("intent"),
                confidence=confidence,
            )
        
        # 4. Execute on per-user HA instance
        # TODO: Call per-user HA instance based on user_id
        # For now, return LLM response directly
        ha_response = {
            "state": "executed",
            "entity_id": intent_data.get("target", {}).get("name", "unknown")
        }
        
        # 5. Generate response text (from LLM or enhanced based on HA result)
        response_text = intent_data.get("response", "Parancs feldolgozva.")
        
        # 6. Log to audit trail
        latency_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "intent_success",
            request_id=request_id,
            user_id=request.user_id,
            intent=intent_data.get("intent"),
            confidence=confidence,
            latency_ms=latency_ms,
        )
        
        # TODO: Persist audit log to DB using AsyncSession
        
        return IntentResponse(
            request_id=request_id,
            intent=intent_data.get("intent", "unknown"),
            entity_id=intent_data.get("target", {}).get("name"),
            response=response_text,
            status=IntentStatus.SUCCESS.value,
            confidence=confidence,
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
async def process_intent_batch(
    requests: list[IntentRequest],
    authorization: str = Header(None),
):
    """Batch intent processing"""
    responses = []
    for req in requests:
        single = await process_intent(req, authorization=authorization)
        responses.append(single)
    return responses
