from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.exceptions import BadRequestException, ConflictException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.token import Token
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def register(self, user_in: UserCreate) -> User:
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise ConflictException(
                message=f"User with email '{user_in.email}' already exists",
                error_code="EMAIL_ALREADY_EXISTS",
            )

        hashed_pw = hash_password(user_in.password)
        db_user = User(
            email=user_in.email.lower().strip(),
            full_name=user_in.full_name.strip(),
            hashed_password=hashed_pw,
            is_active=True,
            is_superuser=False,
        )
        self.session.add(db_user)
        await self.session.flush()
        await self.session.refresh(db_user)
        return db_user

    async def authenticate(self, email: str, password: str) -> Token:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedException(
                message="Invalid email or password",
                error_code="INVALID_CREDENTIALS",
            )

        if not user.is_active:
            raise UnauthorizedException(
                message="User account is inactive",
                error_code="INACTIVE_USER",
            )

        access_token = create_access_token(
            subject=user.id,
            extra_claims={"email": user.email, "name": user.full_name},
        )
        refresh_token = create_refresh_token(subject=user.id)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh_access_token(self, refresh_token: str) -> Token:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedException(
                message="Invalid token type for refresh",
                error_code="INVALID_TOKEN_TYPE",
            )

        user_id = int(payload.get("sub"))
        user = await self.user_repo.get(user_id)
        if not user or not user.is_active:
            raise UnauthorizedException(
                message="User not found or inactive",
                error_code="USER_NOT_FOUND",
            )

        new_access_token = create_access_token(
            subject=user.id,
            extra_claims={"email": user.email, "name": user.full_name},
        )
        new_refresh_token = create_refresh_token(subject=user.id)

        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
