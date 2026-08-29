from datetime import datetime
from typing import Any, Dict, Optional
from app.models.base import ActivityAction
from app.schemas.common import SchemaBase


class ActivityLogResponse(SchemaBase):
    id: int
    workspace_id: int
    actor_id: Optional[int] = None
    actor_name: Optional[str] = None
    action: ActivityAction
    entity_type: str
    entity_id: int
    details: Optional[Dict[str, Any]] = None
    created_at: datetime
