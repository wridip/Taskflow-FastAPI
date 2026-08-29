from typing import Generic, List, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class SchemaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class PaginationMeta(BaseModel):
    page: int = Field(ge=1, description="Current page number")
    size: int = Field(ge=1, description="Number of items per page")
    total_items: int = Field(ge=0, description="Total count of matching items")
    total_pages: int = Field(ge=0, description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_previous: bool = Field(description="Whether there is a previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T] = Field(description="List of records for the current page")
    meta: PaginationMeta = Field(description="Pagination metadata")


class MessageResponse(BaseModel):
    message: str
    success: bool = True


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    environment: str
