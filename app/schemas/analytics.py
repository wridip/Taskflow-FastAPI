from typing import Dict, List, Optional
from app.models.base import TaskPriority, TaskStatus
from app.schemas.common import SchemaBase


class MemberWorkload(SchemaBase):
    user_id: int
    user_name: str
    user_email: str
    assigned_tasks_count: int
    completed_tasks_count: int
    pending_tasks_count: int


class WorkspaceAnalyticsResponse(SchemaBase):
    workspace_id: int
    total_projects: int
    total_tasks: int
    completed_tasks: int
    completion_rate: float
    overdue_tasks: int
    tasks_by_status: Dict[str, int]
    tasks_by_priority: Dict[str, int]
    member_workloads: List[MemberWorkload]
