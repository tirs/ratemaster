"""Auth schemas."""
from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    """User signup request."""

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="Password")


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="Password")


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Seconds until expiry")
