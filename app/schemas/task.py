from datetime import datetime
from typing import List, Optional
from pydantic import Field
from app.models.base import TaskPriority, TaskStatus
from app.schemas.common import SchemaBase


class TaskBase(SchemaBase):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    assignee_id: Optional[int] = None
    tags: Optional[str] = Field(None, max_length=255)


class TaskCreate(TaskBase):
    pass


class TaskUpdate(SchemaBase):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    assignee_id: Optional[int] = None
    tags: Optional[str] = Field(None, max_length=255)


class TaskStatusUpdate(SchemaBase):
    status: TaskStatus


class TaskAssignUpdate(SchemaBase):
    assignee_id: Optional[int] = None


class TaskResponse(TaskBase):
    id: int
    project_id: int
    reporter_id: Optional[int] = None
    assignee_name: Optional[str] = None
    reporter_name: Optional[str] = None
    comments_count: int = 0
    created_at: datetime
    updated_at: datetime


class TaskFilterParams(SchemaBase):
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_id: Optional[int] = None
    search: Optional[str] = None
    due_before: Optional[datetime] = None
    due_after: Optional[datetime] = None
    sort_by: str = "created_at"  # created_at, due_date, priority, status, title
    sort_dir: str = "desc"       # asc, desc
    page: int = 1
    size: int = 20
