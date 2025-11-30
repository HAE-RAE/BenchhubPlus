"""Security utilities for BenchHub Plus."""

import base64
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple, Union

import httpx
from fastapi import Cookie, HTTPException
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet

from .config import get_settings

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _build_fernet(secret: str) -> Fernet:
    """Build a Fernet instance from the provided secret key."""
    digest = hashlib.sha256(secret.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(digest)
    return Fernet(fernet_key)


_fernet = _build_fernet(settings.secret_key)


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def generate_api_key() -> str:
    """Generate secure API key."""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash API key for secure storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def encrypt_secret(value: str) -> str:
    """Encrypt sensitive value for storage."""
    return _fernet.encrypt(value.encode()).decode()


def decrypt_secret(value: str) -> str:
    """Decrypt stored sensitive value."""
    return _fernet.decrypt(value.encode()).decode()


def sanitize_model_name(model_name: str) -> str:
    """Sanitize model name for safe storage."""
    # Remove potentially dangerous characters
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    sanitized = "".join(c for c in model_name if c in safe_chars)
    
    # Limit length
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    
    return sanitized


def validate_api_endpoint(endpoint: str) -> bool:
    """Validate API endpoint URL."""
    # Basic validation - in production, you might want more sophisticated checks
    if not endpoint.startswith(("http://", "https://")):
        return False
    
    # Check for common malicious patterns
    malicious_patterns = [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "file://",
        "ftp://",
    ]
    
    endpoint_lower = endpoint.lower()
    for pattern in malicious_patterns:
        if pattern in endpoint_lower:
            return False
    
    return True


def mask_api_key(api_key: str) -> str:
    """Mask API key for logging/display purposes."""
    if len(api_key) <= 8:
        return "*" * len(api_key)
    
    return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]

def create_jwt_token(user_id: int, email: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=settings.access_token_expire_hours)
    
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    encoded_jwt = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def verify_jwt_token(token: str) -> Dict[str, Any]:
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expired"
        )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


async def get_google_user_info(code: str) -> Dict[str, Any]:
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uri": settings.google_redirect_uri,
        "grant_type": "authorization_code",
    }
    
    async with httpx.AsyncClient() as client:
        try:
            token_response = await client.post(token_url, data=token_data)
            token_response.raise_for_status()
            token_json = token_response.json()
            access_token = token_json.get("access_token")
            
            if not access_token:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to get access token from Google"
                )
            
            user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {"Authorization": f"Bearer {access_token}"}
            user_response = await client.get(user_info_url, headers=headers)
            user_response.raise_for_status()
            user_info = user_response.json()
            
            return user_info
            
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get user info from Google: {str(e)}"
            )

class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed for given identifier."""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        # Initialize if not exists
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        # Check if under limit
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True
    
    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests for identifier."""
        if identifier not in self.requests:
            return self.max_requests
        
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        return max(0, self.max_requests - len(self.requests[identifier]))


# Global rate limiter instance
rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_per_minute,
    window_seconds=60
)


class RedisRateLimiter:
    """Rate limiter backed by Redis for multi-instance deployments."""

    def __init__(
        self,
        redis_client: "redis.asyncio.Redis",
        max_requests: int = 60,
        window_seconds: int = 60,
    ) -> None:
        self.redis = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def is_allowed(self, identifier: str) -> Tuple[bool, int]:
        """Check allowance and return (allowed, remaining)."""

        key = f"rate:{identifier or 'anonymous'}"
        now = int(time.time())
        window_start = now - self.window_seconds

        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(key, "-inf", window_start)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, self.window_seconds)
            _, _, count, _ = await pipe.execute()

        remaining = max(0, self.max_requests - count)
        allowed = count <= self.max_requests
        return allowed, remaining

    async def get_remaining(self, identifier: str) -> int:
        """Return remaining quota for identifier."""
        allowed, remaining = await self.is_allowed(identifier)
        return remaining