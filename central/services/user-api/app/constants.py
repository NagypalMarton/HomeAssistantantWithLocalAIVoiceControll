"""
Application constants and enums
"""

from enum import Enum


class UserRole(str, Enum):
    """User role types"""
    USER = "user"
    ADMIN = "admin"


class IntentStatus(str, Enum):
    """Intent processing status"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    NOT_IMPLEMENTED = "not_implemented"


class ComponentStatus(str, Enum):
    """Service component status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class TokenType(str, Enum):
    """Token types"""
    BEARER = "bearer"


# Field length constants
EMAIL_MAX_LENGTH = 255
PASSWORD_HASH_LENGTH = 255
HA_INSTANCE_URL_LENGTH = 255
DEVICE_ID_MAX_LENGTH = 255
REQUEST_ID_LENGTH = 255
ROLE_MAX_LENGTH = 20
STATUS_MAX_LENGTH = 20

# Request text limits
TEXT_MIN_LENGTH = 1
TEXT_MAX_LENGTH = 1000

# Validation messages
VALIDATION_EMAIL_REQUIRED = "Email is required"
VALIDATION_PASSWORD_REQUIRED = "Password is required"
VALIDATION_PASSWORD_MIN_LENGTH = "Password must be at least 8 characters"
VALIDATION_TEXT_REQUIRED = "Text is required"
VALIDATION_TEXT_TOO_LONG = "Text exceeds maximum length"
VALIDATION_USER_ID_REQUIRED = "User ID is required"
VALIDATION_DEVICE_ID_REQUIRED = "Device ID is required"
