from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.project import Project
from app.models.task import Task
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, session: AsyncSession):
        super().__init__(Project, session)

    async def list_by_workspace(
        self,
        workspace_id: int,
        include_archived: bool = False,
    ) -> List[dict]:
        # Query projects with task count
        stmt = (
            select(
                Project,
                func.count(Task.id).label("task_count"),
            )
            .outerjoin(Task, Task.project_id == Project.id)
            .where(Project.workspace_id == workspace_id)
        )
        if not include_archived:
            stmt = stmt.where(Project.is_archived.is_(False))

        stmt = stmt.group_by(Project.id).order_by(Project.created_at.desc())
        result = await self.session.execute(stmt)

        projects_with_counts = []
        for project, task_count in result.all():
            projects_with_counts.append({
                "project": project,
                "task_count": task_count,
            })
        return projects_with_counts

    async def get_with_task_count(self, project_id: int) -> Optional[dict]:
        stmt = (
            select(
                Project,
                func.count(Task.id).label("task_count"),
            )
            .outerjoin(Task, Task.project_id == Project.id)
            .where(Project.id == project_id)
            .group_by(Project.id)
        )
        result = await self.session.execute(stmt)
        row = result.first()
        if not row:
            return None
        return {
            "project": row[0],
            "task_count": row[1],
        }
