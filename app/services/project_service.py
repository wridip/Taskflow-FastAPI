from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException
from app.models.base import ActivityAction, WorkspaceRole
from app.models.project import Project
from app.repositories.activity_repo import ActivityRepository
from app.repositories.project_repo import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.workspace_service import WorkspaceService


class ProjectService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.project_repo = ProjectRepository(session)
        self.workspace_service = WorkspaceService(session)
        self.activity_repo = ActivityRepository(session)

    async def create_project(
        self,
        workspace_id: int,
        user_id: int,
        project_in: ProjectCreate,
    ) -> ProjectResponse:
        await self.workspace_service.check_membership(
            workspace_id,
            user_id,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.MEMBER],
        )

        project = Project(
            workspace_id=workspace_id,
            name=project_in.name.strip(),
            description=project_in.description.strip() if project_in.description else None,
            created_by_id=user_id,
        )
        self.session.add(project)
        await self.session.flush()
        await self.session.refresh(project)

        await self.activity_repo.record_activity(
            workspace_id=workspace_id,
            actor_id=user_id,
            action=ActivityAction.CREATED,
            entity_type="PROJECT",
            entity_id=project.id,
            details={"project_name": project.name},
        )

        return ProjectResponse(
            id=project.id,
            workspace_id=project.workspace_id,
            name=project.name,
            description=project.description,
            is_archived=project.is_archived,
            created_by_id=project.created_by_id,
            created_at=project.created_at,
            updated_at=project.updated_at,
            task_count=0,
        )

    async def list_workspace_projects(
        self,
        workspace_id: int,
        user_id: int,
        include_archived: bool = False,
    ) -> List[ProjectResponse]:
        await self.workspace_service.check_membership(workspace_id, user_id)

        rows = await self.project_repo.list_by_workspace(workspace_id, include_archived=include_archived)
        return [
            ProjectResponse(
                id=r["project"].id,
                workspace_id=r["project"].workspace_id,
                name=r["project"].name,
                description=r["project"].description,
                is_archived=r["project"].is_archived,
                created_by_id=r["project"].created_by_id,
                created_at=r["project"].created_at,
                updated_at=r["project"].updated_at,
                task_count=r["task_count"],
            )
            for r in rows
        ]

    async def get_project(self, project_id: int, user_id: int) -> ProjectResponse:
        data = await self.project_repo.get_with_task_count(project_id)
        if not data:
            raise NotFoundException(message="Project not found", error_code="PROJECT_NOT_FOUND")

        project = data["project"]
        await self.workspace_service.check_membership(project.workspace_id, user_id)

        return ProjectResponse(
            id=project.id,
            workspace_id=project.workspace_id,
            name=project.name,
            description=project.description,
            is_archived=project.is_archived,
            created_by_id=project.created_by_id,
            created_at=project.created_at,
            updated_at=project.updated_at,
            task_count=data["task_count"],
        )

    async def update_project(
        self,
        project_id: int,
        user_id: int,
        update_in: ProjectUpdate,
    ) -> ProjectResponse:
        project = await self.project_repo.get(project_id)
        if not project:
            raise NotFoundException(message="Project not found", error_code="PROJECT_NOT_FOUND")

        await self.workspace_service.check_membership(
            project.workspace_id,
            user_id,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.MEMBER],
        )

        if update_in.name is not None:
            project.name = update_in.name.strip()
        if update_in.description is not None:
            project.description = update_in.description.strip()
        if update_in.is_archived is not None:
            project.is_archived = update_in.is_archived

        updated = await self.project_repo.update(project, {})
        data = await self.project_repo.get_with_task_count(project_id)

        await self.activity_repo.record_activity(
            workspace_id=project.workspace_id,
            actor_id=user_id,
            action=ActivityAction.UPDATED,
            entity_type="PROJECT",
            entity_id=project.id,
            details={"updated_fields": list(update_in.model_dump(exclude_unset=True).keys())},
        )

        return ProjectResponse(
            id=updated.id,
            workspace_id=updated.workspace_id,
            name=updated.name,
            description=updated.description,
            is_archived=updated.is_archived,
            created_by_id=updated.created_by_id,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
            task_count=data["task_count"] if data else 0,
        )

    async def delete_project(self, project_id: int, user_id: int) -> None:
        project = await self.project_repo.get(project_id)
        if not project:
            raise NotFoundException(message="Project not found", error_code="PROJECT_NOT_FOUND")

        await self.workspace_service.check_membership(
            project.workspace_id,
            user_id,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.ADMIN],
        )

        await self.project_repo.delete(project)
        await self.activity_repo.record_activity(
            workspace_id=project.workspace_id,
            actor_id=user_id,
            action=ActivityAction.DELETED,
            entity_type="PROJECT",
            entity_id=project_id,
            details={"project_name": project.name},
        )
