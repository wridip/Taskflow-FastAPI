from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(tags=["Projects"])


@router.post(
    "/workspaces/{workspace_id}/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="Create a project within a workspace. Requires OWNER, ADMIN, or MEMBER role.",
)
async def create_project(
    workspace_id: int,
    project_in: ProjectCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectResponse:
    service = ProjectService(session)
    return await service.create_project(workspace_id, current_user.id, project_in)


@router.get(
    "/workspaces/{workspace_id}/projects",
    response_model=List[ProjectResponse],
    status_code=status.HTTP_200_OK,
    summary="List workspace projects",
    description="Retrieve all projects belonging to a specific workspace.",
)
async def list_workspace_projects(
    workspace_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    include_archived: bool = Query(False, description="Include archived projects in results"),
) -> List[ProjectResponse]:
    service = ProjectService(session)
    return await service.list_workspace_projects(
        workspace_id,
        current_user.id,
        include_archived=include_archived,
    )


@router.get(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Get project details",
    description="Retrieve specific project information by ID.",
)
async def get_project(
    project_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectResponse:
    service = ProjectService(session)
    return await service.get_project(project_id, current_user.id)


@router.patch(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Update project",
    description="Update project name, description, or archive status.",
)
async def update_project(
    project_id: int,
    update_in: ProjectUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectResponse:
    service = ProjectService(session)
    return await service.update_project(project_id, current_user.id, update_in)


@router.delete(
    "/projects/{project_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete project",
    description="Permanently delete a project and all its tasks. Requires OWNER or ADMIN role.",
)
async def delete_project(
    project_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    service = ProjectService(session)
    await service.delete_project(project_id, current_user.id)
    return MessageResponse(message="Project deleted successfully")
