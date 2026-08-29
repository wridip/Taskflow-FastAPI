from datetime import datetime
from typing import Annotated, List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.base import TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentResponse
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.task import (
    TaskCreate,
    TaskFilterParams,
    TaskResponse,
    TaskStatusUpdate,
    TaskUpdate,
)
from app.services.task_service import TaskService

router = APIRouter(tags=["Tasks & Comments"])


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    description="Create a task inside a project. Triggers an async background notification if an assignee is provided.",
)
async def create_task(
    project_id: int,
    task_in: TaskCreate,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TaskResponse:
    service = TaskService(session)
    return await service.create_task(
        project_id=project_id,
        user_id=current_user.id,
        task_in=task_in,
        background_tasks=background_tasks,
    )


@router.get(
    "/projects/{project_id}/tasks",
    response_model=PaginatedResponse[TaskResponse],
    status_code=status.HTTP_200_OK,
    summary="List & filter project tasks",
    description="Retrieve paginated list of tasks in a project with flexible filtering by status, priority, assignee, due date, and keyword search.",
)
async def list_project_tasks(
    project_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by task priority"),
    assignee_id: Optional[int] = Query(None, description="Filter by assigned user ID"),
    search: Optional[str] = Query(None, description="Search in task title, description, and tags"),
    due_before: Optional[datetime] = Query(None, description="Filter tasks due on or before this datetime"),
    due_after: Optional[datetime] = Query(None, description="Filter tasks due on or after this datetime"),
    sort_by: str = Query("created_at", description="Field to sort by: created_at, due_date, priority, status, title"),
    sort_dir: str = Query("desc", description="Sort direction: asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE, description="Items per page"),
) -> PaginatedResponse[TaskResponse]:
    params = TaskFilterParams(
        status=status,
        priority=priority,
        assignee_id=assignee_id,
        search=search,
        due_before=due_before,
        due_after=due_after,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        size=size,
    )
    service = TaskService(session)
    return await service.list_project_tasks(
        project_id=project_id,
        user_id=current_user.id,
        params=params,
    )


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Get task details",
    description="Retrieve task details including comments count and assignee info.",
)
async def get_task(
    task_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TaskResponse:
    service = TaskService(session)
    return await service.get_task(task_id, current_user.id)


@router.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Update task",
    description="Update task fields including title, description, status, priority, due date, or assignee.",
)
async def update_task(
    task_id: int,
    task_in: TaskUpdate,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TaskResponse:
    service = TaskService(session)
    return await service.update_task(
        task_id=task_id,
        user_id=current_user.id,
        task_in=task_in,
        background_tasks=background_tasks,
    )


@router.patch(
    "/tasks/{task_id}/status",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Quick status update",
    description="Update only the task status. Triggers notification to the reporter.",
)
async def update_task_status(
    task_id: int,
    status_in: TaskStatusUpdate,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TaskResponse:
    service = TaskService(session)
    return await service.update_task_status(
        task_id=task_id,
        user_id=current_user.id,
        status_in=status_in,
        background_tasks=background_tasks,
    )


@router.delete(
    "/tasks/{task_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete task",
    description="Permanently remove a task and its comments.",
)
async def delete_task(
    task_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    service = TaskService(session)
    await service.delete_task(task_id, current_user.id)
    return MessageResponse(message="Task deleted successfully")


# Comments
@router.post(
    "/tasks/{task_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add comment to task",
    description="Post a comment on a specific task.",
)
async def add_comment(
    task_id: int,
    comment_in: CommentCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CommentResponse:
    service = TaskService(session)
    return await service.add_comment(task_id, current_user.id, comment_in)


@router.get(
    "/tasks/{task_id}/comments",
    response_model=List[CommentResponse],
    status_code=status.HTTP_200_OK,
    summary="List task comments",
    description="Retrieve all comments for a given task.",
)
async def list_comments(
    task_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> List[CommentResponse]:
    service = TaskService(session)
    return await service.list_comments(task_id, current_user.id)
