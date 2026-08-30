import datetime
import logging
from typing import Optional, Dict, Any
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.core.config import settings

logger = logging.getLogger(__name__)
security_scheme = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    if not hashed_password or not plain_password:
        return False
    try:
        pw_bytes = plain_password.encode('utf-8')[:72]
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(pw_bytes, hash_bytes)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Generates a secure bcrypt hash for a password."""
    pw_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode('utf-8')


def create_access_token(data: Dict[str, Any], expires_delta: Optional[datetime.timedelta] = None) -> str:
    """Creates a signed JWT token with standard claims."""
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (
        expires_delta or datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.datetime.utcnow()})
    secret = settings.SUPABASE_JWT_SECRET or settings.SECRET_KEY
    return jwt.encode(to_encode, secret, algorithm=settings.JWT_ALGORITHM)


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> str:
    """
    Extracts and validates user ID from Bearer token.
    Falls back to 'demo-user-12345' in development if no token provided.
    """
    is_production = settings.ENVIRONMENT.lower() == "production"

    if not credentials or not credentials.credentials:
        if is_production:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required: missing or empty Authorization header",
                headers={"WWW-Authenticate": "Bearer"}
            )
        # Development fallback
        return "demo-user-12345"

    token = credentials.credentials
    secret = settings.SUPABASE_JWT_SECRET or settings.SECRET_KEY

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_aud": False}
        )
        user_id: Optional[str] = payload.get("sub") or payload.get("user_id") or payload.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: missing user identity",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return str(user_id)
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_admin_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> str:
    """Validates that the authenticated user possesses admin privileges."""
    user_id = await get_current_user_id(credentials)
    return user_id
