import json
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.activity_log import ActivityLog
from app.models.base import ActivityAction
from app.repositories.base import BaseRepository


class ActivityRepository(BaseRepository[ActivityLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(ActivityLog, session)

    async def record_activity(
        self,
        workspace_id: int,
        action: ActivityAction,
        entity_type: str,
        entity_id: int,
        actor_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> ActivityLog:
        details_str = json.dumps(details) if details else None
        log = ActivityLog(
            workspace_id=workspace_id,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details_str,
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def list_by_workspace(self, workspace_id: int, limit: int = 50) -> List[dict]:
        stmt = (
            select(ActivityLog)
            .where(ActivityLog.workspace_id == workspace_id)
            .options(selectinload(ActivityLog.actor))
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        logs = list(result.scalars().all())

        parsed = []
        for log in logs:
            parsed_details = None
            if log.details:
                try:
                    parsed_details = json.loads(log.details)
                except Exception:
                    parsed_details = {"raw": log.details}

            parsed.append({
                "id": log.id,
                "workspace_id": log.workspace_id,
                "actor_id": log.actor_id,
                "actor_name": log.actor.full_name if log.actor else "System",
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "details": parsed_details,
                "created_at": log.created_at,
            })
        return parsed
