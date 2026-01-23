"""
Middleware for request tracking and logging
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import time
import structlog

logger = structlog.get_logger()

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add request ID to all requests"""
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests and responses"""
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = getattr(request.state, "request_id", "unknown")
        
        logger.info(
            "request_received",
            method=request.method,
            path=request.url.path,
            request_id=request_id,
        )
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=int(process_time * 1000),
            request_id=request_id,
        )
        
        return response
