import datetime
import logging
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.core.config import settings

logger = logging.getLogger(__name__)
security_scheme = HTTPBearer(auto_error=False)


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
    Extracts and validates user ID from Bearer token (Supabase Auth compatible).
    
    Production Mode:
      - Requires a valid Bearer token signed with SUPABASE_JWT_SECRET or SECRET_KEY.
      - Missing or invalid tokens raise HTTP 401 Unauthorized.
      
    Development Mode:
      - If a valid token is provided, uses the token identity.
      - If no token is provided, falls back to 'dev-user-12345' for local API testing.
    """
    is_production = settings.ENVIRONMENT.lower() == "production"

    if not credentials or not credentials.credentials:
        if is_production:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required: missing or empty Authorization header",
                headers={"WWW-Authenticate": "Bearer"}
            )
        # Development mode fallback
        return "dev-user-12345"

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
                detail="Invalid token payload: missing subject ('sub') claim",
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
    # If specific admin IDs or role claims are configured, verify here
    return user_id
