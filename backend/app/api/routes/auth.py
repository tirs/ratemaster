"""Auth API routes."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status

logger = logging.getLogger(__name__)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse
from app.services.auth import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
async def signup(
    body: SignupRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Create new user account and return JWT."""
    try:
        result = await db.execute(select(User).where(User.email == body.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        user = User(
            email=body.email,
            hashed_password=hash_password(body.password),
        )
        db.add(user)
        await db.flush()
        token = create_access_token(subject=user.id)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.jwt_expire_minutes * 60,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Signup failed: %s", e)
        raise


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate and return JWT."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token(subject=user.id)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.jwt_expire_minutes * 60,
    )
