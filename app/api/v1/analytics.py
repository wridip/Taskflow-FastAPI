from typing import Annotated, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.activity_log import ActivityLogResponse
from app.schemas.analytics import WorkspaceAnalyticsResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(tags=["Analytics & Audit Logs"])


@router.get(
    "/workspaces/{workspace_id}/analytics",
    response_model=WorkspaceAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get workspace analytics",
    description="Retrieve aggregated metrics including task counts, completion rate, overdue tasks, priority breakdown, and per-member workload distribution.",
)
async def get_workspace_analytics(
    workspace_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WorkspaceAnalyticsResponse:
    service = AnalyticsService(session)
    return await service.get_workspace_analytics(workspace_id, current_user.id)


@router.get(
    "/workspaces/{workspace_id}/activity",
    response_model=List[ActivityLogResponse],
    status_code=status.HTTP_200_OK,
    summary="Get workspace activity timeline",
    description="Retrieve the latest audit trail events and user actions across the workspace.",
)
async def get_workspace_activity(
    workspace_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(50, ge=1, le=100, description="Max number of activity events to return"),
) -> List[ActivityLogResponse]:
    service = AnalyticsService(session)
    logs = await service.get_workspace_activity(workspace_id, current_user.id, limit=limit)
    return [ActivityLogResponse(**log) for log in logs]
