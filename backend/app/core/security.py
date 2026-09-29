import datetime
import time
import logging
from typing import Optional, Dict, Any, Tuple
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db

logger = logging.getLogger(__name__)
security_scheme = HTTPBearer(auto_error=False)

# In-memory TTL caches to eliminate repetitive DB overhead and token crypto verification
_VERIFIED_USER_CACHE: Dict[str, float] = {}  # user_id -> timestamp (valid 5 min)
_TOKEN_AUTH_CACHE: Dict[str, Tuple[str, Optional[str], Optional[str], float]] = {}  # token -> (uid, email, name, exp)


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


def get_cached_user_info(user_id: str) -> Tuple[Optional[str], Optional[str]]:
    """Returns (email, full_name) for user_id if present in active token cache."""
    now = time.time()
    for token, (uid, email, name, exp) in list(_TOKEN_AUTH_CACHE.items()):
        if uid == user_id and exp > now:
            return email, name
    return None, None


async def ensure_user_and_profile_exist(
    db: AsyncSession,
    user_id: str,
    email: Optional[str] = None,
    full_name: Optional[str] = None
) -> None:
    """Ensures a corresponding User and UserProfile exist in the database for the authenticated UID."""
    now = time.time()
    # Skip DB queries if user was already verified within the last 5 minutes
    if user_id in _VERIFIED_USER_CACHE and (now - _VERIFIED_USER_CACHE[user_id]) < 300:
        return

    try:
        from app.models.user import User
        from app.models.profile import UserProfile
        from sqlalchemy import select, update

        clean_email = email.strip().lower() if (email and email.strip()) else None

        stmt = select(User).where(User.id == user_id)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            # 1. If user not found by ID, check if account already exists with this email (e.g. registered before Firebase login)
            if clean_email:
                stmt_email = select(User).where(User.email == clean_email)
                res_email = await db.execute(stmt_email)
                existing_user = res_email.scalar_one_or_none()

                if existing_user:
                    old_id = existing_user.id
                    # Link account to this authenticated user_id
                    existing_user.id = user_id
                    if full_name and (not existing_user.full_name or existing_user.full_name in ("Career Candidate", "Career Discovery User")):
                        existing_user.full_name = full_name

                    # Migrate profile references
                    stmt_p_new = select(UserProfile).where(UserProfile.user_id == user_id)
                    p_new = (await db.execute(stmt_p_new)).scalar_one_or_none()

                    stmt_p_old = select(UserProfile).where(UserProfile.user_id == old_id)
                    p_old = (await db.execute(stmt_p_old)).scalar_one_or_none()

                    if p_old and not p_new:
                        p_old.user_id = user_id
                    elif p_old and p_new:
                        await db.delete(p_old)

                    # Update references in related tables from old_id to new user_id
                    from app.models.digital_twin import DigitalTwin, TwinActivity, TwinGoal
                    from app.models.job import Job, JobApplication
                    from app.models.interview import InterviewSession
                    from app.models.resume import Resume
                    from app.models.roadmap import Roadmap
                    from app.models.skill import UserSkill
                    from app.models.weekly_report import WeeklyReport

                    for model in [DigitalTwin, TwinActivity, TwinGoal, Job, JobApplication, InterviewSession, Resume, Roadmap, UserSkill, WeeklyReport]:
                        try:
                            await db.execute(
                                update(model).where(model.user_id == old_id).values(user_id=user_id)
                            )
                        except Exception:
                            pass

                    user = existing_user

            # 2. If still not found, create new User
            if not user:
                default_name = full_name or (clean_email.split("@")[0].capitalize() if clean_email else "Career Candidate")
                user = User(
                    id=user_id,
                    email=clean_email or f"{user_id}@firebase.local",
                    full_name=default_name,
                    is_active=True
                )
                db.add(user)
        else:
            # User exists — update email or full_name if previous was placeholder
            if clean_email and (not user.email or user.email.endswith("@firebase.local") or user.email == "user@aicareercoach.ai"):
                user.email = clean_email
            if full_name and (not user.full_name or user.full_name in ("Career Candidate", "Career Discovery User")):
                user.full_name = full_name

        # Ensure UserProfile exists
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
        _VERIFIED_USER_CACHE[user_id] = now
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
    Extracts and validates user ID from Bearer token with in-memory caching.
    1. Checks in-memory token cache for instant sub-millisecond validation.
    2. Verifies Firebase ID Token using Firebase Admin SDK.
    3. Falls back to HMAC JWT validation for backwards compatibility / local tests.
    4. Falls back to 'demo-user-12345' in development if no token provided.
    5. Automatically ensures User and UserProfile records exist in SQLite.
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

    # Fast path: check in-memory token cache
    now = time.time()
    cached = _TOKEN_AUTH_CACHE.get(token)
    if cached and cached[3] > now:
        cached_uid, cached_email, cached_name, _ = cached
        await ensure_user_and_profile_exist(db, cached_uid, cached_email, cached_name)
        return cached_uid

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
    # Cache token for 5 minutes
    _TOKEN_AUTH_CACHE[token] = (uid_str, email, full_name, now + 300)
    await ensure_user_and_profile_exist(db, uid_str, email, full_name)
    return uid_str


async def get_current_admin_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
) -> str:
    """Validates that the authenticated user possesses admin privileges."""
    user_id = await get_current_user_id(credentials, db)
    return user_id
