from datetime import datetime
from typing import Optional
from pydantic import Field
from app.schemas.common import SchemaBase


class CommentCreate(SchemaBase):
    content: str = Field(min_length=1, max_length=5000)


class CommentResponse(SchemaBase):
    id: int
    task_id: int
    author_id: Optional[int] = None
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    content: str
    created_at: datetime
    updated_at: datetime
