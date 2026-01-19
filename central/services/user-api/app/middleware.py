"""
Middleware for request tracking and logging
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import structlog
import time

logger = structlog.get_logger()

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    """Log HTTP requests and responses"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = getattr(request.state, "request_id", "unknown")
        start_time = time.time()
        
        logger.info(
            "http.request",
            method=request.method,
            path=request.url.path,
            request_id=request_id,
        )
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        logger.info(
            "http.response",
            status_code=response.status_code,
            duration_ms=int(duration * 1000),
            request_id=request_id,
        )
        
        return response
