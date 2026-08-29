from typing import Annotated
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import UnauthorizedException
from app.core.security import decode_token
from app.models.user import User
from app.repositories.user_repo import UserRepository

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token",
    auto_error=False,
)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if not token:
        raise UnauthorizedException(
            message="Authentication credentials were not provided",
            error_code="NOT_AUTHENTICATED",
        )

    payload = decode_token(token)
    if payload.get("type") != "access":
        raise UnauthorizedException(
            message="Invalid token type, access token required",
            error_code="INVALID_TOKEN_TYPE",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException(
            message="Could not validate credentials",
            error_code="INVALID_TOKEN_PAYLOAD",
        )

    user_repo = UserRepository(session)
    user = await user_repo.get(int(user_id))
    if not user:
        raise UnauthorizedException(
            message="User associated with token no longer exists",
            error_code="USER_NOT_FOUND",
        )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise UnauthorizedException(
            message="Inactive user account",
            error_code="INACTIVE_USER",
        )
    return current_user


async def get_current_superuser(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    if not current_user.is_superuser:
        raise UnauthorizedException(
            message="Superuser privileges required",
            error_code="SUPERUSER_REQUIRED",
        )
    return current_user
