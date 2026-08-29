from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.token import PasswordChangeRequest
from app.schemas.user import UserProfileResponse, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Retrieve full profile details and workspace membership counts for the currently authenticated user.",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserProfileResponse:
    user_service = UserService(session)
    return await user_service.get_profile(current_user.id)


@router.patch(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
    description="Update email or full name of the currently authenticated user.",
)
async def update_me(
    user_in: UserUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    user_service = UserService(session)
    updated_user = await user_service.update_profile(current_user.id, user_in)
    return UserResponse.model_validate(updated_user)


@router.post(
    "/me/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Change user password",
    description="Change password by verifying the current password and setting a new one.",
)
async def change_password(
    req: PasswordChangeRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    user_service = UserService(session)
    await user_service.change_password(current_user.id, req)
    return MessageResponse(message="Password successfully updated")
