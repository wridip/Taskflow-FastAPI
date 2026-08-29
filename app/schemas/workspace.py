from datetime import datetime
from typing import List, Optional
from pydantic import EmailStr, Field
from app.models.base import WorkspaceRole
from app.schemas.common import SchemaBase


class WorkspaceBase(SchemaBase):
    name: str = Field(min_length=2, max_length=100)
    slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = Field(None, max_length=500)


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceUpdate(SchemaBase):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class WorkspaceMemberResponse(SchemaBase):
    id: int
    workspace_id: int
    user_id: int
    user_email: str
    user_full_name: str
    role: WorkspaceRole
    created_at: datetime


class WorkspaceMemberCreate(SchemaBase):
    email: EmailStr
    role: WorkspaceRole = WorkspaceRole.MEMBER


class WorkspaceMemberUpdate(SchemaBase):
    role: WorkspaceRole


class WorkspaceResponse(WorkspaceBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime


class WorkspaceDetailResponse(WorkspaceResponse):
    members: List[WorkspaceMemberResponse] = []
    projects_count: int = 0
