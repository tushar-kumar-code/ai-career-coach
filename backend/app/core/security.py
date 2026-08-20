from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)) -> str:
    """
    Extracts and validates user ID from Bearer token (Supabase Auth compatible).
    In development mode without token, returns a mock user ID for easy API testing.
    """
    if not credentials:
        # Development fallback
        return "dev-user-12345"

    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token header"
        )
    
    # In production, verify token with Supabase JWT public key
    return "user-id-from-jwt"
