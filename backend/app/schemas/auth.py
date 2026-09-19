"""
Authentication Schemas for QUANTLAB API.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="Valid institutional or personal email address")
    password: str = Field(..., min_length=6, max_length=128, description="Password (min 6 characters)")
    full_name: Optional[str] = Field(None, max_length=255, description="Full name or analyst handle")


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., description="Account password")


class UserResponse(BaseModel):
    id: int = Field(..., description="Unique user ID")
    email: str = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, description="Full name or analyst handle")
    is_active: bool = Field(True, description="Account active status")
    created_at: datetime = Field(..., description="Account creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT Bearer access token")
    token_type: str = Field("bearer", description="Token authorization type")
    user: UserResponse = Field(..., description="Authenticated user profile")


class MessageResponse(BaseModel):
    message: str = Field(..., description="Status or confirmation message")
