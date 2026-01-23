"""
Custom exceptions for the application
"""

from fastapi import HTTPException, status


class AuthenticationError(HTTPException):
    """Authentication failed"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class AuthorizationError(HTTPException):
    """Authorization failed"""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ValidationError(HTTPException):
    """Validation failed"""
    def __init__(self, detail: str = "Validation error"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class NotFoundError(HTTPException):
    """Resource not found"""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class DatabaseError(HTTPException):
    """Database operation failed"""
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


class ExternalServiceError(HTTPException):
    """External service call failed"""
    def __init__(self, detail: str = "External service error", service: str = "unknown"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{service}: {detail}"
        )


class HomeAssistantError(ExternalServiceError):
    """Home Assistant API error"""
    def __init__(self, detail: str = "Home Assistant API error"):
        super().__init__(detail=detail, service="HomeAssistant")


class LLMError(ExternalServiceError):
    """LLM (Ollama) service error"""
    def __init__(self, detail: str = "LLM service error"):
        super().__init__(detail=detail, service="Ollama")



class LLMServiceError(ExternalServiceError):
    """LLM service error"""
    def __init__(self, detail: str = "LLM service error"):
        super().__init__(detail=detail, service="Ollama")
