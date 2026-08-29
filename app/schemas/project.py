from datetime import datetime
from typing import Optional
from pydantic import Field
from app.schemas.common import SchemaBase


class ProjectBase(SchemaBase):
    name: str = Field(min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(SchemaBase):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    is_archived: Optional[bool] = None


class ProjectResponse(ProjectBase):
    id: int
    workspace_id: int
    is_archived: bool
    created_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    task_count: int = 0
