from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.activity_repo import ActivityRepository
from app.repositories.task_repo import TaskRepository
from app.schemas.analytics import WorkspaceAnalyticsResponse
from app.services.workspace_service import WorkspaceService


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.task_repo = TaskRepository(session)
        self.activity_repo = ActivityRepository(session)
        self.workspace_service = WorkspaceService(session)

    async def get_workspace_analytics(self, workspace_id: int, user_id: int) -> WorkspaceAnalyticsResponse:
        await self.workspace_service.check_membership(workspace_id, user_id)
        raw_stats = await self.task_repo.get_workspace_analytics(workspace_id)
        return WorkspaceAnalyticsResponse(**raw_stats)

    async def get_workspace_activity(self, workspace_id: int, user_id: int, limit: int = 50) -> list:
        await self.workspace_service.check_membership(workspace_id, user_id)
        return await self.activity_repo.list_by_workspace(workspace_id, limit=limit)
