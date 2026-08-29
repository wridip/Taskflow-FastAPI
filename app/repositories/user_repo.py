from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(func.lower(User.email) == email.lower().strip())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_counts(self, user_id: int) -> dict:
        owned_stmt = select(func.count(Workspace.id)).where(Workspace.owner_id == user_id)
        owned_res = await self.session.execute(owned_stmt)
        owned_count = owned_res.scalar_one() or 0

        member_stmt = select(func.count(WorkspaceMember.id)).where(WorkspaceMember.user_id == user_id)
        member_res = await self.session.execute(member_stmt)
        member_count = member_res.scalar_one() or 0

        return {
            "owned_workspaces_count": owned_count,
            "memberships_count": member_count,
        }
