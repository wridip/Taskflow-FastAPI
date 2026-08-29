from datetime import datetime, timezone
import math
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.base import TaskPriority, TaskStatus
from app.models.comment import Comment
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.models.workspace_member import WorkspaceMember
from app.repositories.base import BaseRepository
from app.schemas.task import TaskFilterParams


class TaskRepository(BaseRepository[Task]):
    def __init__(self, session: AsyncSession):
        super().__init__(Task, session)

    async def get_by_id_with_relations(self, task_id: int) -> Optional[dict]:
        stmt = (
            select(
                Task,
                User.full_name.label("assignee_name"),
                func.count(Comment.id).label("comments_count"),
            )
            .outerjoin(User, User.id == Task.assignee_id)
            .outerjoin(Comment, Comment.task_id == Task.id)
            .where(Task.id == task_id)
            .options(
                selectinload(Task.reporter),
                selectinload(Task.assignee),
            )
            .group_by(Task.id, User.full_name)
        )
        result = await self.session.execute(stmt)
        row = result.first()
        if not row:
            return None

        task, assignee_name, comments_count = row
        return {
            "task": task,
            "assignee_name": assignee_name,
            "reporter_name": task.reporter.full_name if task.reporter else None,
            "comments_count": comments_count,
        }

    async def filter_and_paginate(
        self,
        project_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
        params: Optional[TaskFilterParams] = None,
    ) -> Tuple[List[dict], int, int]:
        """Filter, sort, and paginate tasks. Returns (items, total_items, total_pages)."""
        params = params or TaskFilterParams()

        base_query = (
            select(
                Task,
                User.full_name.label("assignee_name"),
                func.count(Comment.id).label("comments_count"),
            )
            .outerjoin(User, User.id == Task.assignee_id)
            .outerjoin(Comment, Comment.task_id == Task.id)
            .options(
                selectinload(Task.reporter),
                selectinload(Task.assignee),
            )
        )

        if project_id:
            base_query = base_query.where(Task.project_id == project_id)
        elif workspace_id:
            base_query = base_query.join(Project, Project.id == Task.project_id).where(
                Project.workspace_id == workspace_id
            )

        # Filters
        if params.status:
            base_query = base_query.where(Task.status == params.status)
        if params.priority:
            base_query = base_query.where(Task.priority == params.priority)
        if params.assignee_id:
            base_query = base_query.where(Task.assignee_id == params.assignee_id)
        if params.search:
            search_term = f"%{params.search.strip()}%"
            base_query = base_query.where(
                or_(
                    Task.title.ilike(search_term),
                    Task.description.ilike(search_term),
                    Task.tags.ilike(search_term),
                )
            )
        if params.due_before:
            base_query = base_query.where(Task.due_date <= params.due_before)
        if params.due_after:
            base_query = base_query.where(Task.due_date >= params.due_after)

        # Group by
        base_query = base_query.group_by(Task.id, User.full_name)

        # Count total items
        count_subquery = base_query.subquery()
        count_stmt = select(func.count()).select_from(count_subquery)
        total_result = await self.session.execute(count_stmt)
        total_items = total_result.scalar_one() or 0

        # Sorting
        sort_col = getattr(Task, params.sort_by, Task.created_at)
        order_fn = desc if params.sort_dir.lower() == "desc" else asc
        base_query = base_query.order_by(order_fn(sort_col))

        # Pagination
        offset = (params.page - 1) * params.size
        base_query = base_query.offset(offset).limit(params.size)

        result = await self.session.execute(base_query)
        items = []
        for task, assignee_name, comments_count in result.all():
            items.append({
                "task": task,
                "assignee_name": assignee_name,
                "reporter_name": task.reporter.full_name if task.reporter else None,
                "comments_count": comments_count,
            })

        total_pages = math.ceil(total_items / params.size) if params.size > 0 else 0
        return items, total_items, total_pages

    async def get_workspace_analytics(self, workspace_id: int) -> Dict[str, Any]:
        """Compute full workspace analytics including status, priority, and workload distribution."""
        now = datetime.now(timezone.utc)

        # 1. Total projects count
        proj_stmt = select(func.count(Project.id)).where(
            Project.workspace_id == workspace_id,
            Project.is_archived.is_(False),
        )
        proj_res = await self.session.execute(proj_stmt)
        total_projects = proj_res.scalar_one() or 0

        # 2. Total tasks count
        tasks_stmt = (
            select(func.count(Task.id))
            .join(Project, Project.id == Task.project_id)
            .where(Project.workspace_id == workspace_id)
        )
        tasks_res = await self.session.execute(tasks_stmt)
        total_tasks = tasks_res.scalar_one() or 0

        # 3. Completed tasks count
        completed_stmt = (
            select(func.count(Task.id))
            .join(Project, Project.id == Task.project_id)
            .where(
                Project.workspace_id == workspace_id,
                Task.status == TaskStatus.DONE,
            )
        )
        completed_res = await self.session.execute(completed_stmt)
        completed_tasks = completed_res.scalar_one() or 0

        # 4. Overdue tasks count
        overdue_stmt = (
            select(func.count(Task.id))
            .join(Project, Project.id == Task.project_id)
            .where(
                Project.workspace_id == workspace_id,
                Task.status != TaskStatus.DONE,
                Task.due_date < now,
            )
        )
        overdue_res = await self.session.execute(overdue_stmt)
        overdue_tasks = overdue_res.scalar_one() or 0

        # 5. Tasks by status
        status_stmt = (
            select(Task.status, func.count(Task.id))
            .join(Project, Project.id == Task.project_id)
            .where(Project.workspace_id == workspace_id)
            .group_by(Task.status)
        )
        status_res = await self.session.execute(status_stmt)
        tasks_by_status = {status.value: count for status, count in status_res.all()}
        for s in TaskStatus:
            if s.value not in tasks_by_status:
                tasks_by_status[s.value] = 0

        # 6. Tasks by priority
        priority_stmt = (
            select(Task.priority, func.count(Task.id))
            .join(Project, Project.id == Task.project_id)
            .where(Project.workspace_id == workspace_id)
            .group_by(Task.priority)
        )
        priority_res = await self.session.execute(priority_stmt)
        tasks_by_priority = {prio.value: count for prio, count in priority_res.all()}
        for p in TaskPriority:
            if p.value not in tasks_by_priority:
                tasks_by_priority[p.value] = 0

        # 7. Member workloads
        members_stmt = (
            select(WorkspaceMember)
            .where(WorkspaceMember.workspace_id == workspace_id)
            .options(selectinload(WorkspaceMember.user))
        )
        members_res = await self.session.execute(members_stmt)
        members = list(members_res.scalars().all())

        member_workloads = []
        for m in members:
            # total assigned
            assigned_stmt = (
                select(func.count(Task.id))
                .join(Project, Project.id == Task.project_id)
                .where(
                    Project.workspace_id == workspace_id,
                    Task.assignee_id == m.user_id,
                )
            )
            a_res = await self.session.execute(assigned_stmt)
            assigned_count = a_res.scalar_one() or 0

            # completed assigned
            done_stmt = (
                select(func.count(Task.id))
                .join(Project, Project.id == Task.project_id)
                .where(
                    Project.workspace_id == workspace_id,
                    Task.assignee_id == m.user_id,
                    Task.status == TaskStatus.DONE,
                )
            )
            d_res = await self.session.execute(done_stmt)
            done_count = d_res.scalar_one() or 0

            member_workloads.append({
                "user_id": m.user_id,
                "user_name": m.user.full_name,
                "user_email": m.user.email,
                "assigned_tasks_count": assigned_count,
                "completed_tasks_count": done_count,
                "pending_tasks_count": assigned_count - done_count,
            })

        completion_rate = round((completed_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0.0

        return {
            "workspace_id": workspace_id,
            "total_projects": total_projects,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": completion_rate,
            "overdue_tasks": overdue_tasks,
            "tasks_by_status": tasks_by_status,
            "tasks_by_priority": tasks_by_priority,
            "member_workloads": member_workloads,
        }
