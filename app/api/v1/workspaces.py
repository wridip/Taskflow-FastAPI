from typing import Annotated, List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceDetailResponse,
    WorkspaceMemberCreate,
    WorkspaceMemberResponse,
    WorkspaceMemberUpdate,
    WorkspaceResponse,
    WorkspaceUpdate,
)
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new workspace",
    description="Create an organization/team workspace. The creating user is automatically assigned as OWNER.",
)
async def create_workspace(
    workspace_in: WorkspaceCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WorkspaceResponse:
    service = WorkspaceService(session)
    workspace = await service.create_workspace(current_user.id, workspace_in)
    return WorkspaceResponse.model_validate(workspace)


@router.get(
    "",
    response_model=List[WorkspaceResponse],
    status_code=status.HTTP_200_OK,
    summary="List user workspaces",
    description="Retrieve all workspaces that the authenticated user belongs to.",
)
async def list_workspaces(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> List[WorkspaceResponse]:
    service = WorkspaceService(session)
    workspaces = await service.list_user_workspaces(current_user.id)
    return [WorkspaceResponse.model_validate(w) for w in workspaces]


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get workspace details",
    description="Retrieve workspace details including member roster and total projects count.",
)
async def get_workspace(
    workspace_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WorkspaceDetailResponse:
    service = WorkspaceService(session)
    return await service.get_workspace_details(workspace_id, current_user.id)


@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_200_OK,
    summary="Update workspace",
    description="Update workspace name or description. Requires OWNER or ADMIN role.",
)
async def update_workspace(
    workspace_id: int,
    update_in: WorkspaceUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WorkspaceResponse:
    service = WorkspaceService(session)
    workspace = await service.update_workspace(workspace_id, current_user.id, update_in)
    return WorkspaceResponse.model_validate(workspace)


@router.delete(
    "/{workspace_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete workspace",
    description="Permanently delete a workspace and all nested projects/tasks. Requires OWNER role.",
)
async def delete_workspace(
    workspace_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    service = WorkspaceService(session)
    await service.delete_workspace(workspace_id, current_user.id)
    return MessageResponse(message="Workspace deleted successfully")


# Membership & RBAC endpoints
@router.post(
    "/{workspace_id}/members",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add member to workspace",
    description="Add an existing registered user to the workspace with a specific role (ADMIN, MEMBER, VIEWER). Requires OWNER or ADMIN.",
)
async def add_member(
    workspace_id: int,
    member_in: WorkspaceMemberCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WorkspaceMemberResponse:
    service = WorkspaceService(session)
    return await service.add_member(workspace_id, current_user.id, member_in)


@router.patch(
    "/{workspace_id}/members/{user_id}",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_200_OK,
    summary="Update member role",
    description="Update the workspace role for a member. Requires OWNER or ADMIN.",
)
async def update_member_role(
    workspace_id: int,
    user_id: int,
    update_in: WorkspaceMemberUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WorkspaceMemberResponse:
    service = WorkspaceService(session)
    return await service.update_member_role(workspace_id, user_id, current_user.id, update_in)


@router.delete(
    "/{workspace_id}/members/{user_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove member from workspace",
    description="Remove a user from the workspace. Requires OWNER or ADMIN.",
)
async def remove_member(
    workspace_id: int,
    user_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    service = WorkspaceService(session)
    await service.remove_member(workspace_id, user_id, current_user.id)
    return MessageResponse(message="Member removed successfully")
