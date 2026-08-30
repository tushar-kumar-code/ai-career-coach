from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password (min 6 chars)")
    full_name: Optional[str] = Field(default=None, description="User display name")


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class ResetPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="User registered email address")
    new_password: str = Field(..., min_length=6, description="New password (min 6 characters)")


class SendOTPRequest(BaseModel):
    email: EmailStr = Field(..., description="User registered email address")
    purpose: Optional[str] = Field(default="login", description="Purpose of OTP: 'login' or 'reset'")


class VerifyOTPLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User registered email address")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")


class VerifyOTPResetRequest(BaseModel):
    email: EmailStr = Field(..., description="User registered email address")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")
    new_password: str = Field(..., min_length=6, description="New password (min 6 chars)")


class OTPResponse(BaseModel):
    email: str
    message: str
    dev_code: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
