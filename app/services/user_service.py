from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.token import PasswordChangeRequest
from app.schemas.user import UserProfileResponse, UserUpdate


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def get_profile(self, user_id: int) -> UserProfileResponse:
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundException(message="User not found", error_code="USER_NOT_FOUND")

        counts = await self.user_repo.get_user_counts(user_id)
        return UserProfileResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            owned_workspaces_count=counts["owned_workspaces_count"],
            memberships_count=counts["memberships_count"],
        )

    async def update_profile(self, user_id: int, user_in: UserUpdate) -> User:
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundException(message="User not found", error_code="USER_NOT_FOUND")

        if user_in.email and user_in.email.lower() != user.email.lower():
            existing = await self.user_repo.get_by_email(user_in.email)
            if existing:
                raise ConflictException(
                    message=f"Email '{user_in.email}' is already taken",
                    error_code="EMAIL_TAKEN",
                )
            user.email = user_in.email.lower().strip()

        if user_in.full_name:
            user.full_name = user_in.full_name.strip()

        return await self.user_repo.update(user, {})

    async def change_password(self, user_id: int, req: PasswordChangeRequest) -> None:
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundException(message="User not found", error_code="USER_NOT_FOUND")

        if not verify_password(req.current_password, user.hashed_password):
            raise BadRequestException(
                message="Current password is incorrect",
                error_code="INVALID_CURRENT_PASSWORD",
            )

        user.hashed_password = hash_password(req.new_password)
        await self.user_repo.update(user, {})
