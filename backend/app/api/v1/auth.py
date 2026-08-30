import logging
import uuid
import random
import time
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user_id
)
from app.models.user import User
from app.models.profile import UserProfile
from app.schemas.health import APIResponse
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    ResetPasswordRequest,
    SendOTPRequest,
    VerifyOTPLoginRequest,
    VerifyOTPResetRequest,
    OTPResponse,
    UserResponse,
    AuthResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory OTP storage: { "email": {"code": "123456", "expires_at": float_ts, "purpose": "login"} }
_OTP_CACHE: Dict[str, Dict[str, Any]] = {}
OTP_EXPIRY_SECONDS = 600  # 10 minutes validity


def _generate_otp_code() -> str:
    """Generate a random 6-digit verification security code."""
    return f"{random.randint(100000, 999999)}"


@router.post("/register", response_model=APIResponse[AuthResponse], summary="Register a new user account")
async def register(req: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    email_clean = req.email.strip().lower()

    # 1. Check existing user
    stmt = select(User).where(User.email == email_clean)
    res = await db.execute(stmt)
    existing_user = res.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # 2. Create User
    new_user_id = str(uuid.uuid4())
    hashed_pwd = get_password_hash(req.password)
    user = User(
        id=new_user_id,
        email=email_clean,
        full_name=req.full_name.strip() if req.full_name else email_clean.split("@")[0].capitalize(),
        hashed_password=hashed_pwd,
        is_active=True
    )
    db.add(user)

    # 3. Create initial UserProfile
    profile = UserProfile(
        user_id=new_user_id,
        target_career="Software Developer",
        primary_archetype="Systems Builder",
        skills_matrix={}
    )
    db.add(profile)
    await db.commit()
    await db.refresh(user)

    # 4. Generate JWT token
    token = create_access_token(data={"sub": user.id, "email": user.email, "name": user.full_name})

    return APIResponse(
        success=True,
        data=AuthResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                is_superuser=user.is_superuser
            )
        ),
        message="Registration successful"
    )


@router.post("/login", response_model=APIResponse[AuthResponse], summary="Authenticate user and return JWT access token")
async def login(req: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    email_clean = req.email.strip().lower()

    # 1. Find user by email
    stmt = select(User).where(User.email == email_clean)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user or not user.hashed_password or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials or try signing in with OTP / Another Way."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been disabled."
        )

    # 2. Issue JWT token
    token = create_access_token(data={"sub": user.id, "email": user.email, "name": user.full_name})

    return APIResponse(
        success=True,
        data=AuthResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                is_superuser=user.is_superuser
            )
        ),
        message="Login successful"
    )


@router.post("/send-otp", response_model=APIResponse[OTPResponse], summary="Send / Generate 6-digit OTP code for 2FA / Login / Reset")
async def send_otp(req: SendOTPRequest, db: AsyncSession = Depends(get_db)):
    email_clean = req.email.strip().lower()

    # Check if user exists or auto-create candidate identity for OTP login
    stmt = select(User).where(User.email == email_clean)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        if req.purpose == "reset":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account found with this email address. Please check your email or register."
            )
        # For OTP login, auto-register new candidate if doesn't exist
        new_user_id = str(uuid.uuid4())
        user = User(
            id=new_user_id,
            email=email_clean,
            full_name=email_clean.split("@")[0].capitalize(),
            hashed_password=get_password_hash(f"otp_user_{int(time.time())}"),
            is_active=True
        )
        db.add(user)
        profile = UserProfile(
            user_id=new_user_id,
            target_career="Software Developer",
            primary_archetype="Systems Builder",
            skills_matrix={}
        )
        db.add(profile)
        await db.commit()

    code = _generate_otp_code()
    _OTP_CACHE[email_clean] = {
        "code": code,
        "expires_at": time.time() + OTP_EXPIRY_SECONDS,
        "purpose": req.purpose or "login"
    }

    logger.info(f"Generated 2FA / OTP code for {email_clean}: {code}")

    return APIResponse(
        success=True,
        data=OTPResponse(
            email=email_clean,
            message=f"6-digit verification code generated! Valid for 10 minutes.",
            dev_code=code  # Conveniently provided for instant local verification
        ),
        message="Verification code sent successfully"
    )


@router.post("/verify-otp-login", response_model=APIResponse[AuthResponse], summary="2FA / OTP instant login")
async def verify_otp_login(req: VerifyOTPLoginRequest, db: AsyncSession = Depends(get_db)):
    email_clean = req.email.strip().lower()
    otp_data = _OTP_CACHE.get(email_clean)

    if not otp_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active verification code found for this email. Please request a new code."
        )

    if time.time() > otp_data["expires_at"]:
        _OTP_CACHE.pop(email_clean, None)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired. Please request a new code."
        )

    if otp_data["code"] != req.otp.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code. Please check and try again."
        )

    # Valid OTP -> clean up cache
    _OTP_CACHE.pop(email_clean, None)

    # Fetch user
    stmt = select(User).where(User.email == email_clean)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found.")

    token = create_access_token(data={"sub": user.id, "email": user.email, "name": user.full_name})

    return APIResponse(
        success=True,
        data=AuthResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                is_superuser=user.is_superuser
            )
        ),
        message="2FA Verification successful! Logged in."
    )


@router.post("/verify-otp-reset", response_model=APIResponse[dict], summary="Reset password using 2FA OTP verification code")
async def verify_otp_reset(req: VerifyOTPResetRequest, db: AsyncSession = Depends(get_db)):
    email_clean = req.email.strip().lower()
    otp_data = _OTP_CACHE.get(email_clean)

    if not otp_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active verification code found. Please request a new code."
        )

    if time.time() > otp_data["expires_at"]:
        _OTP_CACHE.pop(email_clean, None)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired. Please request a new code."
        )

    if otp_data["code"] != req.otp.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code. Please check and try again."
        )

    _OTP_CACHE.pop(email_clean, None)

    stmt = select(User).where(User.email == email_clean)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found.")

    user.hashed_password = get_password_hash(req.new_password)
    await db.commit()

    return APIResponse(
        success=True,
        data={"email": user.email},
        message="Password reset successfully verified with 2FA code! You can now log in."
    )


@router.post("/demo-login", response_model=APIResponse[AuthResponse], summary="1-Click Instant Demo Login")
async def demo_login(db: AsyncSession = Depends(get_db)):
    demo_email = "demo@aicareercoach.ai"
    stmt = select(User).where(User.email == demo_email)
    res = await db.execute(stmt)
    demo_user = res.scalar_one_or_none()

    if not demo_user:
        demo_id = "demo-user-12345"
        demo_user = User(
            id=demo_id,
            email=demo_email,
            full_name="Demo Candidate",
            hashed_password=get_password_hash("demo12345"),
            is_active=True
        )
        db.add(demo_user)

        # Also ensure UserProfile exists
        stmt_p = select(UserProfile).where(UserProfile.user_id == demo_id)
        res_p = await db.execute(stmt_p)
        if not res_p.scalar_one_or_none():
            demo_profile = UserProfile(
                user_id=demo_id,
                target_career="Software Developer",
                primary_archetype="Systems Builder",
                skills_matrix={"Python": {"level": "Proficient", "verified": True}}
            )
            db.add(demo_profile)

        await db.commit()
        await db.refresh(demo_user)

    token = create_access_token(data={"sub": demo_user.id, "email": demo_user.email, "name": demo_user.full_name})

    return APIResponse(
        success=True,
        data=AuthResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse(
                id=demo_user.id,
                email=demo_user.email,
                full_name=demo_user.full_name,
                is_active=demo_user.is_active,
                is_superuser=demo_user.is_superuser
            )
        ),
        message="Logged in as Demo User"
    )


@router.get("/me", response_model=APIResponse[UserResponse], summary="Get current logged in user profile")
async def get_me(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        # Fallback profile for dev identity
        return APIResponse(
            success=True,
            data=UserResponse(
                id=user_id,
                email="user@aicareercoach.ai",
                full_name="Career Discovery User",
                is_active=True
            ),
            message="User profile fetched"
        )

    return APIResponse(
        success=True,
        data=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser
        ),
        message="User profile fetched"
    )


@router.post("/reset-password", response_model=APIResponse[dict], summary="Reset user password using registered email")
async def reset_password(req: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    email_clean = req.email.strip().lower()

    stmt = select(User).where(User.email == email_clean)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email address. Please verify your email or register a new account."
        )

    # Update to new hashed password
    user.hashed_password = get_password_hash(req.new_password)
    await db.commit()

    return APIResponse(
        success=True,
        data={"email": user.email},
        message="Your password has been successfully reset! You can now log in with your new password."
    )
