from datetime import datetime
from typing import Optional
from pydantic import EmailStr, Field
from app.schemas.common import SchemaBase


class UserBase(SchemaBase):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=100)


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=100)


class UserLogin(SchemaBase):
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)


class UserUpdate(SchemaBase):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime


class UserProfileResponse(UserResponse):
    owned_workspaces_count: int = 0
    memberships_count: int = 0
