"""
Security utilities for password hashing and JWT token management
"""

from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from cryptography.fernet import Fernet
from app.config import settings
from app.exceptions import AuthenticationError

# Password hashing context
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# Token encryption cipher
_cipher_suite = None

def _get_cipher_suite() -> Fernet:
    """Get or initialize the cipher suite for token encryption"""
    global _cipher_suite
    if _cipher_suite is None:
        _cipher_suite = Fernet(settings.encryption_key.encode())
    return _cipher_suite


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Payload data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token
    
    Args:
        data: Payload data to encode in the token
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> dict:
    """
    Verify and decode a JWT token
    
    Args:
        token: JWT token string
        token_type: Expected token type ('access' or 'refresh')
        
    Returns:
        Decoded token payload
        
    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        
        # Verify token type
        if payload.get("type") != token_type:
            raise AuthenticationError(f"Invalid token type. Expected {token_type}")
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None:
            raise AuthenticationError("Token has no expiration")
        
        if datetime.fromtimestamp(exp) < datetime.utcnow():
            raise AuthenticationError("Token has expired")
        
        return payload
        
    except JWTError as e:
        raise AuthenticationError(f"Could not validate credentials: {str(e)}")


def get_user_id_from_token(token: str) -> str:
    """
    Extract user ID from JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        User ID string
        
    Raises:
        AuthenticationError: If token is invalid or missing user ID
    """
    payload = verify_token(token)
    user_id = payload.get("sub")
    
    if user_id is None:
        raise AuthenticationError("Token missing user ID")
    
    return user_id


def encrypt_token(plain_token: str) -> str:
    """
    Encrypt a sensitive token (e.g., Home Assistant token)
    
    Args:
        plain_token: Plain text token to encrypt
        
    Returns:
        Encrypted token string (base64-encoded)
    """
    cipher = _get_cipher_suite()
    encrypted = cipher.encrypt(plain_token.encode())
    return encrypted.decode()


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt a sensitive token (e.g., Home Assistant token)
    
    Args:
        encrypted_token: Encrypted token string (base64-encoded)
        
    Returns:
        Plain text token
        
    Raises:
        AuthenticationError: If decryption fails
    """
    try:
        cipher = _get_cipher_suite()
        decrypted = cipher.decrypt(encrypted_token.encode())
        return decrypted.decode()
    except Exception as e:
        raise AuthenticationError(f"Failed to decrypt token: {str(e)}")
