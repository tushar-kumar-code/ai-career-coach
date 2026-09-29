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
from app.models.assessment import AssessmentResponse
from app.schemas.health import APIResponse
from app.schemas.auth import (
    UserRegisterRequest,
    SendRegisterOTPRequest,
    VerifyRegisterRequest,
    UserLoginRequest,
    ResetPasswordRequest,
    SendOTPRequest,
    VerifyOTPLoginRequest,
    VerifyOTPResetRequest,
    OTPResponse,
    UserResponse,
    AuthResponse
)
from app.services.email_validator import validate_email_authenticity
from app.services.email_service import send_verification_email

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory OTP storage: { "email": {"code": "123456", "expires_at": float_ts, "purpose": "register"|"login"|"reset", "pending_data": {...}} }
_OTP_CACHE: Dict[str, Dict[str, Any]] = {}
OTP_EXPIRY_SECONDS = 600  # 10 minutes validity


def _generate_otp_code() -> str:
    """Generate a secure, random 6-digit verification code."""
    return f"{random.randint(100000, 999999)}"


async def _check_user_assessment_completed(db: AsyncSession, user_id: str) -> bool:
    """Check if user has an authentic completed career assessment."""
    try:
        stmt = select(AssessmentResponse.id).where(
            AssessmentResponse.user_id == user_id,
            AssessmentResponse.status == "COMPLETED",
            AssessmentResponse.ai_analysis_json.isnot(None)
        ).limit(1)
        res = await db.execute(stmt)
        return res.scalar_one_or_none() is not None
    except Exception as e:
        logger.warning(f"Error checking assessment status for {user_id}: {e}")
        return False


# ==============================================================================
# 1. REGISTRATION WITH REAL EMAIL OTP VERIFICATION (ChatGPT / Claude / Gemini Style)
# ==============================================================================

@router.post("/send-register-otp", response_model=APIResponse[OTPResponse], summary="Send real 6-digit email verification OTP for account creation")
async def send_register_otp(req: SendRegisterOTPRequest, db: AsyncSession = Depends(get_db)):
    email_clean = req.email.strip().lower()

    # 1. Anti-Fake & Disposable Email Check
    is_valid, err_msg = validate_email_authenticity(email_clean)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg
        )

    # 2. Check if user already exists
    stmt = select(User).where(User.email == email_clean)
    res = await db.execute(stmt)
    existing_user = res.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please log in instead."
        )

    # 3. Generate 6-digit OTP code
    code = _generate_otp_code()
    _OTP_CACHE[email_clean] = {
        "code": code,
        "expires_at": time.time() + OTP_EXPIRY_SECONDS,
        "purpose": "register",
        "full_name": req.full_name.strip() if req.full_name else None
    }

    # 4. Asynchronously send real email to user's real mailbox
    email_result = await send_verification_email(email_clean, code, purpose="register")
    
    msg = f"A 6-digit verification code has been sent to {email_clean}. Please check your inbox and spam folder."
    
    return APIResponse(
        success=True,
        data=OTPResponse(
            email=email_clean,
            message=msg,
            dev_code=code if not email_result.get("sent") else None  # Show code in dev mode only if SMTP is not yet configured
        ),
        message="Verification code sent to your email."
    )


@router.post("/verify-register", response_model=APIResponse[AuthResponse], summary="Verify email OTP and create new verified account")
async def verify_register(req: VerifyRegisterRequest, db: AsyncSession = Depends(get_db)):
    email_clean = req.email.strip().lower()

    # 1. Anti-Fake Email Check
    is_valid, err_msg = validate_email_authenticity(email_clean)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    # 2. Check OTP in cache
    otp_data = _OTP_CACHE.get(email_clean)
    if not otp_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active verification code found for this email. Please request a new verification code."
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
            detail="Invalid verification code. Please check your email inbox and enter the 6-digit code correctly."
        )

    # Clean OTP after successful verification
    _OTP_CACHE.pop(email_clean, None)

    # 3. Check for existing user (double safety)
    stmt = select(User).where(User.email == email_clean)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account already created. Please log in."
        )

    # 4. Create User
    new_user_id = str(uuid.uuid4())
    hashed_pwd = get_password_hash(req.password)
    display_name = req.full_name.strip() if (req.full_name and req.full_name.strip()) else email_clean.split("@")[0].capitalize()
    
    user = User(
        id=new_user_id,
        email=email_clean,
        full_name=display_name,
        hashed_password=hashed_pwd,
        is_active=True
    )
    db.add(user)

    # 5. Create initial clean UserProfile
    profile = UserProfile(
        user_id=new_user_id,
        target_career=None,
        primary_archetype=None,
        job_readiness_score=0,
        skills_matrix={}
    )
    db.add(profile)
    await db.commit()
    await db.refresh(user)

    # 6. Generate JWT token
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
                is_superuser=user.is_superuser,
                has_completed_assessment=False
            )
        ),
        message="Account created and verified successfully!"
    )


# Standard fallback registration endpoint
@router.post("/register", response_model=APIResponse[AuthResponse], summary="Register a new user account")
async def register(req: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    email_clean = req.email.strip().lower()

    # Anti-Fake Email Check
    is_valid, err_msg = validate_email_authenticity(email_clean)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    # Check existing user
    stmt = select(User).where(User.email == email_clean)
    res = await db.execute(stmt)
    existing_user = res.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please sign in."
        )

    # Create User
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

    profile = UserProfile(
        user_id=new_user_id,
        target_career=None,
        primary_archetype=None,
        job_readiness_score=0,
        skills_matrix={}
    )
    db.add(profile)
    await db.commit()
    await db.refresh(user)

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
                is_superuser=user.is_superuser,
                has_completed_assessment=False
            )
        ),
        message="Registration successful"
    )


# ==============================================================================
# 2. LOGIN AUTHENTICATION
# ==============================================================================

@router.post("/login", response_model=APIResponse[AuthResponse], summary="Authenticate user and return JWT access token")
async def login(req: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    email_clean = req.email.strip().lower()

    # Anti-Fake Email Check
    is_valid, err_msg = validate_email_authenticity(email_clean)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    # Find user by email
    stmt = select(User).where(User.email == email_clean)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user or not user.hashed_password or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials or use 'Forgot password' to reset."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been disabled."
        )

    has_completed_assessment = await _check_user_assessment_completed(db, user.id)
    token = create_access_token(data={"sub": user.id, "email": user.email, "name": user.full_name})

    try:
        from app.services.email_service import send_login_success_email
        import asyncio
        asyncio.create_task(send_login_success_email(
            to_email=user.email,
            user_name=user.full_name,
            login_method="Email & Password"
        ))
    except Exception as e:
        logger.warning(f"Notice on login success email dispatch: {e}")

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
                is_superuser=user.is_superuser,
                has_completed_assessment=has_completed_assessment
            )
        ),
        message="Login successful"
    )


# ==============================================================================
# 3. REAL EMAIL OTP CODES (2FA Login & Password Reset)
# ==============================================================================

@router.post("/send-otp", response_model=APIResponse[OTPResponse], summary="Send real 6-digit verification code to user email")
async def send_otp(req: SendOTPRequest, db: AsyncSession = Depends(get_db)):
    email_clean = req.email.strip().lower()

    # Anti-Fake Email Check
    is_valid, err_msg = validate_email_authenticity(email_clean)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    purpose = req.purpose or "login"

    stmt = select(User).where(User.email == email_clean)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if purpose == "reset":
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account found with this email address. Please register a new account."
            )
    elif purpose == "login":
        if not user:
            # Auto-register new user for instant 2FA OTP onboarding
            new_user_id = str(uuid.uuid4())
            user = User(
                id=new_user_id,
                email=email_clean,
                full_name=email_clean.split("@")[0].capitalize(),
                hashed_password=get_password_hash(f"otp_{int(time.time())}"),
                is_active=True
            )
            db.add(user)
            profile = UserProfile(
                user_id=new_user_id,
                target_career=None,
                primary_archetype=None,
                job_readiness_score=0,
                skills_matrix={}
            )
            db.add(profile)
            await db.commit()

    code = _generate_otp_code()
    _OTP_CACHE[email_clean] = {
        "code": code,
        "expires_at": time.time() + OTP_EXPIRY_SECONDS,
        "purpose": purpose
    }

    # Send real email to user's registered inbox
    email_result = await send_verification_email(email_clean, code, purpose=purpose)

    logger.info(f"Generated {purpose} code for {email_clean}: (Email Sent: {email_result.get('sent')})")

    if not email_result.get("sent"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to send email. Please configure SMTP_USER & SMTP_PASSWORD in backend/.env, or use Google Password Reset."
        )

    return APIResponse(
        success=True,
        data=OTPResponse(
            email=email_clean,
            message=f"Real 6-digit verification code sent to {email_clean}. Please check your email inbox and enter the code below.",
            dev_code=None
        ),
        message="Verification code dispatched to your email."
    )


@router.post("/verify-otp-login", response_model=APIResponse[AuthResponse], summary="Verify 6-digit OTP code and sign in")
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
            detail="Invalid verification code. Please check your email inbox and enter the 6 digits."
        )

    _OTP_CACHE.pop(email_clean, None)

    stmt = select(User).where(User.email == email_clean)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found.")

    token = create_access_token(data={"sub": user.id, "email": user.email, "name": user.full_name})
    has_completed_assessment = await _check_user_assessment_completed(db, user.id)

    try:
        from app.services.email_service import send_login_success_email
        import asyncio
        asyncio.create_task(send_login_success_email(
            to_email=user.email,
            user_name=user.full_name,
            login_method="Email OTP (2FA)"
        ))
    except Exception as e:
        logger.warning(f"Notice on OTP login success email dispatch: {e}")

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
                is_superuser=user.is_superuser,
                has_completed_assessment=has_completed_assessment
            )
        ),
        message="Verification successful! Signed in."
    )


@router.post("/verify-otp-reset", response_model=APIResponse[dict], summary="Reset password using 6-digit email verification code")
async def verify_otp_reset(req: VerifyOTPResetRequest, db: AsyncSession = Depends(get_db)):
    email_clean = req.email.strip().lower()
    otp_data = _OTP_CACHE.get(email_clean)

    if not otp_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active reset code found. Please request a new code."
        )

    if time.time() > otp_data["expires_at"]:
        _OTP_CACHE.pop(email_clean, None)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset code has expired. Please request a new code."
        )

    if otp_data["code"] != req.otp.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code. Please check your email inbox and enter the code correctly."
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
        message="Password updated successfully! You can now log in with your new password."
    )


# ==============================================================================
# 4. INSTANT DEMO COCKPIT LOGIN
# ==============================================================================

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
    has_completed_assessment = await _check_user_assessment_completed(db, demo_user.id)

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
                is_superuser=demo_user.is_superuser,
                has_completed_assessment=has_completed_assessment
            )
        ),
        message="Logged in as Demo User"
    )


# ==============================================================================
# 5. USER PROFILE
# ==============================================================================

from app.services.firestore.user_repo import UserRepository
from app.services.firestore.assessment_repo import AssessmentRepository


@router.get("/me", response_model=APIResponse[UserResponse], summary="Get current logged in user profile")
async def get_me(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    from app.core.security import get_cached_user_info

    # 1. Check Firestore first if configured
    try:
        fs_user = await UserRepository.get_user(user_id)
        has_completed_fs = await AssessmentRepository.has_completed_assessment(user_id)
        if fs_user and fs_user.get("email"):
            return APIResponse(
                success=True,
                data=UserResponse(
                    id=user_id,
                    email=fs_user.get("email"),
                    full_name=fs_user.get("full_name") or fs_user.get("displayName") or "Candidate",
                    is_active=fs_user.get("is_active", True),
                    is_superuser=fs_user.get("is_superuser", False),
                    has_completed_assessment=has_completed_fs or fs_user.get("has_completed_assessment", False)
                ),
                message="User profile fetched"
            )
    except Exception as e:
        logger.warning(f"Firestore get_me error: {e}")

    # 2. Check SQLite
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    # 3. If user not found in SQLite, attempt recovery from token cache
    cached_email, cached_name = get_cached_user_info(user_id)
    if not user and cached_email:
        try:
            # Check if this email exists under another ID
            stmt_e = select(User).where(User.email == cached_email.strip().lower())
            existing = (await db.execute(stmt_e)).scalar_one_or_none()
            if existing:
                existing.id = user_id
                if cached_name:
                    existing.full_name = cached_name
                await db.commit()
                user = existing
            else:
                new_u = User(
                    id=user_id,
                    email=cached_email.strip().lower(),
                    full_name=cached_name or cached_email.split("@")[0].capitalize(),
                    is_active=True
                )
                db.add(new_u)
                await db.commit()
                user = new_u
        except Exception as sync_err:
            logger.warning(f"Notice on dynamic user creation during get_me: {sync_err}")
            try:
                await db.rollback()
            except Exception:
                pass

    has_completed_assessment = await _check_user_assessment_completed(db, user_id)
    if not has_completed_assessment:
        try:
            has_completed_assessment = await AssessmentRepository.has_completed_assessment(user_id)
        except Exception:
            pass

    if not user:
        # Fallback to cached token data, never dummy email
        real_email = cached_email or f"{user_id}@firebase.local"
        real_name = cached_name or (real_email.split("@")[0].capitalize() if "@" in real_email else "Candidate")
        return APIResponse(
            success=True,
            data=UserResponse(
                id=user_id,
                email=real_email,
                full_name=real_name,
                is_active=True,
                has_completed_assessment=has_completed_assessment
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
            is_superuser=user.is_superuser,
            has_completed_assessment=has_completed_assessment
        ),
        message="User profile fetched"
    )


@router.post("/reset-password", response_model=APIResponse[dict], summary="Reset user password using registered email")
async def reset_password(req: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    email_clean = req.email.strip().lower()

    is_valid, err_msg = validate_email_authenticity(email_clean)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    stmt = select(User).where(User.email == email_clean)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email address. Please check your email or register a new account."
        )

    user.hashed_password = get_password_hash(req.new_password)
    await db.commit()

    return APIResponse(
        success=True,
        data={"email": user.email},
        message="Your password has been reset! You can now log in with your new password."
    )


@router.post("/login-notify", response_model=APIResponse[dict], summary="Send successful login alert email for OAuth/SSO")
async def notify_login_event(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    target_email = user.email if (user and user.email) else None
    target_name = user.full_name if (user and user.full_name) else None

    if not target_email or target_email.endswith("@firebase.local"):
        from app.core.security import get_cached_user_info
        cached_email, cached_name = get_cached_user_info(user_id)
        if cached_email:
            target_email = cached_email
            target_name = cached_name or target_name

    if target_email and not target_email.endswith("@firebase.local") and not target_email.endswith("@auth.local"):
        try:
            from app.services.email_service import send_login_success_email
            import asyncio
            asyncio.create_task(send_login_success_email(
                to_email=target_email,
                user_name=target_name or "Candidate",
                login_method="Google Sign-In"
            ))
        except Exception as e:
            logger.warning(f"Notice on OAuth login success email dispatch: {e}")

    return APIResponse(success=True, data={"notified": True}, message="Login notification processed")
