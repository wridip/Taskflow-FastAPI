from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.models.base import ActivityAction, WorkspaceRole
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.repositories.activity_repo import ActivityRepository
from app.repositories.user_repo import UserRepository
from app.repositories.workspace_member_repo import WorkspaceMemberRepository
from app.repositories.workspace_repo import WorkspaceRepository
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceDetailResponse,
    WorkspaceMemberCreate,
    WorkspaceMemberResponse,
    WorkspaceMemberUpdate,
    WorkspaceResponse,
    WorkspaceUpdate,
)


class WorkspaceService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.workspace_repo = WorkspaceRepository(session)
        self.member_repo = WorkspaceMemberRepository(session)
        self.user_repo = UserRepository(session)
        self.activity_repo = ActivityRepository(session)

    async def check_membership(
        self,
        workspace_id: int,
        user_id: int,
        allowed_roles: Optional[List[WorkspaceRole]] = None,
    ) -> WorkspaceMember:
        """Verify user is a member of the workspace and optionally check their role."""
        membership = await self.member_repo.get_membership(workspace_id, user_id)
        if not membership:
            raise ForbiddenException(
                message="You do not have access to this workspace",
                error_code="WORKSPACE_ACCESS_DENIED",
            )

        if allowed_roles and membership.role not in allowed_roles:
            raise ForbiddenException(
                message=f"Action requires one of the following roles: {[r.value for r in allowed_roles]}",
                error_code="INSUFFICIENT_PERMISSIONS",
            )

        return membership

    async def create_workspace(self, user_id: int, workspace_in: WorkspaceCreate) -> Workspace:
        existing = await self.workspace_repo.get_by_slug(workspace_in.slug)
        if existing:
            raise ConflictException(
                message=f"Workspace with slug '{workspace_in.slug}' already exists",
                error_code="SLUG_ALREADY_EXISTS",
            )

        # 1. Create workspace
        workspace = Workspace(
            name=workspace_in.name.strip(),
            slug=workspace_in.slug.lower().strip(),
            description=workspace_in.description.strip() if workspace_in.description else None,
            owner_id=user_id,
        )
        self.session.add(workspace)
        await self.session.flush()
        await self.session.refresh(workspace)

        # 2. Add creator as OWNER
        member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=user_id,
            role=WorkspaceRole.OWNER,
        )
        self.session.add(member)
        await self.session.flush()

        # 3. Record audit activity
        await self.activity_repo.record_activity(
            workspace_id=workspace.id,
            actor_id=user_id,
            action=ActivityAction.CREATED,
            entity_type="WORKSPACE",
            entity_id=workspace.id,
            details={"name": workspace.name, "slug": workspace.slug},
        )

        return workspace

    async def list_user_workspaces(self, user_id: int) -> List[Workspace]:
        return await self.workspace_repo.list_for_user(user_id)

    async def get_workspace_details(self, workspace_id: int, user_id: int) -> WorkspaceDetailResponse:
        await self.check_membership(workspace_id, user_id)

        workspace = await self.workspace_repo.get_with_details(workspace_id)
        if not workspace:
            raise NotFoundException(message="Workspace not found", error_code="WORKSPACE_NOT_FOUND")

        projects_count = await self.workspace_repo.get_projects_count(workspace_id)

        members_dto = [
            WorkspaceMemberResponse(
                id=m.id,
                workspace_id=m.workspace_id,
                user_id=m.user_id,
                user_email=m.user.email,
                user_full_name=m.user.full_name,
                role=m.role,
                created_at=m.created_at,
            )
            for m in workspace.members
        ]

        return WorkspaceDetailResponse(
            id=workspace.id,
            name=workspace.name,
            slug=workspace.slug,
            description=workspace.description,
            owner_id=workspace.owner_id,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
            members=members_dto,
            projects_count=projects_count,
        )

    async def update_workspace(
        self,
        workspace_id: int,
        user_id: int,
        update_in: WorkspaceUpdate,
    ) -> Workspace:
        await self.check_membership(workspace_id, user_id, allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.ADMIN])
        workspace = await self.workspace_repo.get(workspace_id)
        if not workspace:
            raise NotFoundException(message="Workspace not found", error_code="WORKSPACE_NOT_FOUND")

        if update_in.name:
            workspace.name = update_in.name.strip()
        if update_in.description is not None:
            workspace.description = update_in.description.strip()

        updated_ws = await self.workspace_repo.update(workspace, {})
        await self.activity_repo.record_activity(
            workspace_id=workspace.id,
            actor_id=user_id,
            action=ActivityAction.UPDATED,
            entity_type="WORKSPACE",
            entity_id=workspace.id,
            details={"updated_fields": list(update_in.model_dump(exclude_unset=True).keys())},
        )
        return updated_ws

    async def delete_workspace(self, workspace_id: int, user_id: int) -> None:
        await self.check_membership(workspace_id, user_id, allowed_roles=[WorkspaceRole.OWNER])
        workspace = await self.workspace_repo.get(workspace_id)
        if not workspace:
            raise NotFoundException(message="Workspace not found", error_code="WORKSPACE_NOT_FOUND")

        await self.workspace_repo.delete(workspace)

    async def add_member(
        self,
        workspace_id: int,
        actor_id: int,
        member_in: WorkspaceMemberCreate,
    ) -> WorkspaceMemberResponse:
        await self.check_membership(workspace_id, actor_id, allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.ADMIN])

        user = await self.user_repo.get_by_email(member_in.email)
        if not user:
            raise NotFoundException(
                message=f"User with email '{member_in.email}' not found. They must register first.",
                error_code="USER_NOT_FOUND",
            )

        existing_member = await self.member_repo.get_membership(workspace_id, user.id)
        if existing_member:
            raise ConflictException(
                message="User is already a member of this workspace",
                error_code="MEMBER_ALREADY_EXISTS",
            )

        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=user.id,
            role=member_in.role,
        )
        self.session.add(member)
        await self.session.flush()
        await self.session.refresh(member)

        await self.activity_repo.record_activity(
            workspace_id=workspace_id,
            actor_id=actor_id,
            action=ActivityAction.MEMBER_ADDED,
            entity_type="MEMBER",
            entity_id=member.id,
            details={"added_user_email": user.email, "role": member.role.value},
        )

        return WorkspaceMemberResponse(
            id=member.id,
            workspace_id=member.workspace_id,
            user_id=user.id,
            user_email=user.email,
            user_full_name=user.full_name,
            role=member.role,
            created_at=member.created_at,
        )

    async def update_member_role(
        self,
        workspace_id: int,
        target_user_id: int,
        actor_id: int,
        update_in: WorkspaceMemberUpdate,
    ) -> WorkspaceMemberResponse:
        actor_membership = await self.check_membership(
            workspace_id, actor_id, allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
        )

        target_member = await self.member_repo.get_membership(workspace_id, target_user_id)
        if not target_member:
            raise NotFoundException(message="Member not found in workspace", error_code="MEMBER_NOT_FOUND")

        # Admins cannot alter OWNER's role or elevate someone to OWNER
        if target_member.role == WorkspaceRole.OWNER and actor_membership.role != WorkspaceRole.OWNER:
            raise ForbiddenException(
                message="Only the workspace owner can modify the owner's role",
                error_code="INSUFFICIENT_PERMISSIONS",
            )
        if update_in.role == WorkspaceRole.OWNER and actor_membership.role != WorkspaceRole.OWNER:
            raise ForbiddenException(
                message="Only the current owner can transfer ownership",
                error_code="INSUFFICIENT_PERMISSIONS",
            )

        old_role = target_member.role
        target_member.role = update_in.role
        await self.member_repo.update(target_member, {})

        await self.activity_repo.record_activity(
            workspace_id=workspace_id,
            actor_id=actor_id,
            action=ActivityAction.MEMBER_ROLE_UPDATED,
            entity_type="MEMBER",
            entity_id=target_member.id,
            details={"old_role": old_role.value, "new_role": target_member.role.value},
        )

        return WorkspaceMemberResponse(
            id=target_member.id,
            workspace_id=target_member.workspace_id,
            user_id=target_member.user.id,
            user_email=target_member.user.email,
            user_full_name=target_member.user.full_name,
            role=target_member.role,
            created_at=target_member.created_at,
        )

    async def remove_member(self, workspace_id: int, target_user_id: int, actor_id: int) -> None:
        actor_membership = await self.check_membership(
            workspace_id, actor_id, allowed_roles=[WorkspaceRole.OWNER, WorkspaceRole.ADMIN]
        )

        target_member = await self.member_repo.get_membership(workspace_id, target_user_id)
        if not target_member:
            raise NotFoundException(message="Member not found in workspace", error_code="MEMBER_NOT_FOUND")

        if target_member.role == WorkspaceRole.OWNER:
            raise BadRequestException(
                message="Cannot remove workspace owner. Transfer ownership or delete workspace.",
                error_code="CANNOT_REMOVE_OWNER",
            )

        if target_member.role == WorkspaceRole.ADMIN and actor_membership.role != WorkspaceRole.OWNER:
            raise ForbiddenException(
                message="Admins cannot remove other admins",
                error_code="INSUFFICIENT_PERMISSIONS",
            )

        await self.member_repo.delete(target_member)
        await self.activity_repo.record_activity(
            workspace_id=workspace_id,
            actor_id=actor_id,
            action=ActivityAction.MEMBER_REMOVED,
            entity_type="MEMBER",
            entity_id=target_user_id,
            details={"removed_user_id": target_user_id},
        )
