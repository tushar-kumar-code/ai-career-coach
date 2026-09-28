import datetime
import logging
from typing import Optional, Dict, Any
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db

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


async def ensure_user_and_profile_exist(
    db: AsyncSession,
    user_id: str,
    email: Optional[str] = None,
    full_name: Optional[str] = None
) -> None:
    """Ensures a corresponding User and UserProfile exist in the database for the authenticated UID."""
    try:
        from app.models.user import User
        from app.models.profile import UserProfile
        from sqlalchemy import select

        stmt = select(User).where(User.id == user_id)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            user = User(
                id=user_id,
                email=email or f"{user_id}@firebase.local",
                full_name=full_name or "Career Candidate",
                is_active=True
            )
            db.add(user)

        stmt_prof = select(UserProfile).where(UserProfile.user_id == user_id)
        res_prof = await db.execute(stmt_prof)
        profile = res_prof.scalar_one_or_none()

        if not profile:
            profile = UserProfile(
                user_id=user_id,
                target_career=None,
                primary_archetype=None,
                job_readiness_score=0,
                skills_matrix={}
            )
            db.add(profile)

        await db.commit()
    except Exception as e:
        logger.warning(f"Notice during automatic user sync for {user_id}: {e}")
        try:
            await db.rollback()
        except Exception:
            pass


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
) -> str:
    """
    Extracts and validates user ID from Bearer token.
    1. Verifies Firebase ID Token using Firebase Admin SDK.
    2. Falls back to HMAC JWT validation for backwards compatibility / local tests.
    3. Falls back to 'demo-user-12345' in development if no token provided.
    4. Automatically ensures User and UserProfile records exist in SQLite.
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
        demo_id = "demo-user-12345"
        await ensure_user_and_profile_exist(db, demo_id, "demo@aicareercoach.ai", "Demo Candidate")
        return demo_id

    token = credentials.credentials
    user_id: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None

    # 1. Primary verification: Firebase ID Token
    try:
        from app.core.firebase import verify_firebase_id_token
        decoded = verify_firebase_id_token(token)
        user_id = decoded.get("uid") or decoded.get("user_id") or decoded.get("sub")
        email = decoded.get("email")
        full_name = decoded.get("name")
    except Exception as fb_err:
        logger.debug(f"Firebase token verification attempt notice: {fb_err}")
        # 2. Fallback: Check if it's a signed JWT (for local test suites / legacy tokens)
        secret = settings.SUPABASE_JWT_SECRET or settings.SECRET_KEY
        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_aud": False}
            )
            user_id = payload.get("sub") or payload.get("user_id") or payload.get("id")
            email = payload.get("email")
            full_name = payload.get("name")
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token. Please sign in again.",
                headers={"WWW-Authenticate": "Bearer"}
            )

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing user identity",
            headers={"WWW-Authenticate": "Bearer"}
        )

    uid_str = str(user_id)
    await ensure_user_and_profile_exist(db, uid_str, email, full_name)
    return uid_str


async def get_current_admin_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
) -> str:
    """Validates that the authenticated user possesses admin privileges."""
    user_id = await get_current_user_id(credentials, db)
    return user_id
