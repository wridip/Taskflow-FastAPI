from typing import List, Optional
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from app.models.base import ActivityAction, WorkspaceRole
from app.models.comment import Comment
from app.models.task import Task
from app.repositories.activity_repo import ActivityRepository
from app.repositories.comment_repo import CommentRepository
from app.repositories.project_repo import ProjectRepository
from app.repositories.task_repo import TaskRepository
from app.repositories.user_repo import UserRepository
from app.repositories.workspace_member_repo import WorkspaceMemberRepository
from app.schemas.comment import CommentCreate, CommentResponse
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.task import (
    TaskCreate,
    TaskFilterParams,
    TaskResponse,
    TaskStatusUpdate,
    TaskUpdate,
)
from app.services.notification_service import NotificationService
from app.services.workspace_service import WorkspaceService


class TaskService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.task_repo = TaskRepository(session)
        self.project_repo = ProjectRepository(session)
        self.member_repo = WorkspaceMemberRepository(session)
        self.user_repo = UserRepository(session)
        self.comment_repo = CommentRepository(session)
        self.activity_repo = ActivityRepository(session)
        self.workspace_service = WorkspaceService(session)

    async def _get_project_and_check_access(
        self,
        project_id: int,
        user_id: int,
        allowed_roles: Optional[List[WorkspaceRole]] = None,
    ):
        project = await self.project_repo.get(project_id)
        if not project:
            raise NotFoundException(message="Project not found", error_code="PROJECT_NOT_FOUND")

        await self.workspace_service.check_membership(
            project.workspace_id,
            user_id,
            allowed_roles=allowed_roles,
        )
        return project

    async def create_task(
        self,
        project_id: int,
        user_id: int,
        task_in: TaskCreate,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> TaskResponse:
        project = await self._get_project_and_check_access(
            project_id,
            user_id,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.MEMBER],
        )

        assignee = None
        if task_in.assignee_id:
            assignee_member = await self.member_repo.get_membership(project.workspace_id, task_in.assignee_id)
            if not assignee_member:
                raise BadRequestException(
                    message="Assignee is not a member of this workspace",
                    error_code="INVALID_ASSIGNEE",
                )
            assignee = await self.user_repo.get(task_in.assignee_id)

        task = Task(
            project_id=project_id,
            title=task_in.title.strip(),
            description=task_in.description.strip() if task_in.description else None,
            status=task_in.status,
            priority=task_in.priority,
            due_date=task_in.due_date,
            estimated_hours=task_in.estimated_hours,
            assignee_id=task_in.assignee_id,
            reporter_id=user_id,
            tags=task_in.tags,
        )
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)

        # Audit Log
        await self.activity_repo.record_activity(
            workspace_id=project.workspace_id,
            actor_id=user_id,
            action=ActivityAction.CREATED,
            entity_type="TASK",
            entity_id=task.id,
            details={"task_title": task.title, "status": task.status.value, "priority": task.priority.value},
        )

        # Trigger notification
        if assignee and background_tasks:
            background_tasks.add_task(
                NotificationService.send_task_assigned_notification,
                assignee_email=assignee.email,
                assignee_name=assignee.full_name,
                task_title=task.title,
                task_id=task.id,
                project_name=project.name,
            )

        reporter = await self.user_repo.get(user_id)

        return TaskResponse(
            id=task.id,
            project_id=task.project_id,
            title=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            due_date=task.due_date,
            estimated_hours=task.estimated_hours,
            assignee_id=task.assignee_id,
            assignee_name=assignee.full_name if assignee else None,
            reporter_id=task.reporter_id,
            reporter_name=reporter.full_name if reporter else None,
            tags=task.tags,
            comments_count=0,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    async def list_project_tasks(
        self,
        project_id: int,
        user_id: int,
        params: TaskFilterParams,
    ) -> PaginatedResponse[TaskResponse]:
        await self._get_project_and_check_access(project_id, user_id)

        items, total_items, total_pages = await self.task_repo.filter_and_paginate(
            project_id=project_id,
            params=params,
        )

        tasks_dto = [
            TaskResponse(
                id=item["task"].id,
                project_id=item["task"].project_id,
                title=item["task"].title,
                description=item["task"].description,
                status=item["task"].status,
                priority=item["task"].priority,
                due_date=item["task"].due_date,
                estimated_hours=item["task"].estimated_hours,
                assignee_id=item["task"].assignee_id,
                assignee_name=item["assignee_name"],
                reporter_id=item["task"].reporter_id,
                reporter_name=item["reporter_name"],
                tags=item["task"].tags,
                comments_count=item["comments_count"],
                created_at=item["task"].created_at,
                updated_at=item["task"].updated_at,
            )
            for item in items
        ]

        meta = PaginationMeta(
            page=params.page,
            size=params.size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=params.page < total_pages,
            has_previous=params.page > 1,
        )

        return PaginatedResponse(items=tasks_dto, meta=meta)

    async def get_task(self, task_id: int, user_id: int) -> TaskResponse:
        data = await self.task_repo.get_by_id_with_relations(task_id)
        if not data:
            raise NotFoundException(message="Task not found", error_code="TASK_NOT_FOUND")

        task = data["task"]
        await self._get_project_and_check_access(task.project_id, user_id)

        return TaskResponse(
            id=task.id,
            project_id=task.project_id,
            title=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            due_date=task.due_date,
            estimated_hours=task.estimated_hours,
            assignee_id=task.assignee_id,
            assignee_name=data["assignee_name"],
            reporter_id=task.reporter_id,
            reporter_name=data["reporter_name"],
            tags=task.tags,
            comments_count=data["comments_count"],
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    async def update_task(
        self,
        task_id: int,
        user_id: int,
        task_in: TaskUpdate,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> TaskResponse:
        task = await self.task_repo.get(task_id)
        if not task:
            raise NotFoundException(message="Task not found", error_code="TASK_NOT_FOUND")

        project = await self._get_project_and_check_access(
            task.project_id,
            user_id,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.MEMBER],
        )

        prev_assignee_id = task.assignee_id

        if task_in.assignee_id is not None and task_in.assignee_id != task.assignee_id:
            assignee_member = await self.member_repo.get_membership(project.workspace_id, task_in.assignee_id)
            if not assignee_member:
                raise BadRequestException(
                    message="Assignee is not a member of this workspace",
                    error_code="INVALID_ASSIGNEE",
                )
            task.assignee_id = task_in.assignee_id

        if task_in.title is not None:
            task.title = task_in.title.strip()
        if task_in.description is not None:
            task.description = task_in.description.strip()
        if task_in.status is not None:
            task.status = task_in.status
        if task_in.priority is not None:
            task.priority = task_in.priority
        if task_in.due_date is not None:
            task.due_date = task_in.due_date
        if task_in.estimated_hours is not None:
            task.estimated_hours = task_in.estimated_hours
        if task_in.tags is not None:
            task.tags = task_in.tags

        await self.task_repo.update(task, {})

        # Audit Log
        await self.activity_repo.record_activity(
            workspace_id=project.workspace_id,
            actor_id=user_id,
            action=ActivityAction.UPDATED,
            entity_type="TASK",
            entity_id=task.id,
            details={"task_title": task.title},
        )

        # Notify if newly assigned
        if task.assignee_id and task.assignee_id != prev_assignee_id and background_tasks:
            assignee = await self.user_repo.get(task.assignee_id)
            if assignee:
                background_tasks.add_task(
                    NotificationService.send_task_assigned_notification,
                    assignee_email=assignee.email,
                    assignee_name=assignee.full_name,
                    task_title=task.title,
                    task_id=task.id,
                    project_name=project.name,
                )

        return await self.get_task(task.id, user_id)

    async def update_task_status(
        self,
        task_id: int,
        user_id: int,
        status_in: TaskStatusUpdate,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> TaskResponse:
        task = await self.task_repo.get(task_id)
        if not task:
            raise NotFoundException(message="Task not found", error_code="TASK_NOT_FOUND")

        project = await self._get_project_and_check_access(
            task.project_id,
            user_id,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.MEMBER],
        )

        old_status = task.status
        task.status = status_in.status
        await self.task_repo.update(task, {})

        await self.activity_repo.record_activity(
            workspace_id=project.workspace_id,
            actor_id=user_id,
            action=ActivityAction.STATUS_CHANGED,
            entity_type="TASK",
            entity_id=task.id,
            details={"old_status": old_status.value, "new_status": task.status.value},
        )

        if task.reporter_id and background_tasks:
            reporter = await self.user_repo.get(task.reporter_id)
            actor = await self.user_repo.get(user_id)
            if reporter and actor:
                background_tasks.add_task(
                    NotificationService.send_status_changed_notification,
                    reporter_email=reporter.email,
                    task_title=task.title,
                    task_id=task.id,
                    old_status=old_status.value,
                    new_status=task.status.value,
                    updated_by_name=actor.full_name,
                )

        return await self.get_task(task.id, user_id)

    async def delete_task(self, task_id: int, user_id: int) -> None:
        task = await self.task_repo.get(task_id)
        if not task:
            raise NotFoundException(message="Task not found", error_code="TASK_NOT_FOUND")

        project = await self._get_project_and_check_access(
            task.project_id,
            user_id,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.MEMBER],
        )

        await self.task_repo.delete(task)
        await self.activity_repo.record_activity(
            workspace_id=project.workspace_id,
            actor_id=user_id,
            action=ActivityAction.DELETED,
            entity_type="TASK",
            entity_id=task_id,
            details={"task_title": task.title},
        )

    async def add_comment(self, task_id: int, user_id: int, comment_in: CommentCreate) -> CommentResponse:
        task = await self.task_repo.get(task_id)
        if not task:
            raise NotFoundException(message="Task not found", error_code="TASK_NOT_FOUND")

        project = await self._get_project_and_check_access(
            task.project_id,
            user_id,
            allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.MEMBER],
        )

        comment = Comment(
            task_id=task_id,
            author_id=user_id,
            content=comment_in.content.strip(),
        )
        self.session.add(comment)
        await self.session.flush()
        await self.session.refresh(comment)

        author = await self.user_repo.get(user_id)

        await self.activity_repo.record_activity(
            workspace_id=project.workspace_id,
            actor_id=user_id,
            action=ActivityAction.COMMENT_ADDED,
            entity_type="TASK",
            entity_id=task_id,
            details={"comment_id": comment.id},
        )

        return CommentResponse(
            id=comment.id,
            task_id=comment.task_id,
            author_id=comment.author_id,
            author_name=author.full_name if author else None,
            author_email=author.email if author else None,
            content=comment.content,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )

    async def list_comments(self, task_id: int, user_id: int) -> List[CommentResponse]:
        task = await self.task_repo.get(task_id)
        if not task:
            raise NotFoundException(message="Task not found", error_code="TASK_NOT_FOUND")

        await self._get_project_and_check_access(task.project_id, user_id)

        comments = await self.comment_repo.list_by_task(task_id)
        return [
            CommentResponse(
                id=c.id,
                task_id=c.task_id,
                author_id=c.author_id,
                author_name=c.author.full_name if c.author else None,
                author_email=c.author.email if c.author else None,
                content=c.content,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in comments
        ]
