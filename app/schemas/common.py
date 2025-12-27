"""
Common Pydantic schemas used across the application.
"""

from datetime import datetime
from typing import Optional, Generic, TypeVar, List
from uuid import UUID
from pydantic import BaseModel, Field


T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination query parameters."""

    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=50, ge=1, le=100, description="Max records to return")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total count of items")
    skip: int = Field(..., description="Number of skipped items")
    limit: int = Field(..., description="Page size")
    has_next: bool = Field(..., description="Whether there are more pages")

    model_config = {"from_attributes": True}


class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool = Field(default=True)
    message: str = Field(..., description="Success message")


class MessageResponse(BaseModel):
    """Generic message response with success status."""

    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")


class ErrorResponse(BaseModel):
    """Generic error response."""

    detail: str = Field(..., description="Error detail message")
    error_code: Optional[str] = Field(None, description="Application error code")


class TimestampMixin(BaseModel):
    """Mixin for created_at/updated_at timestamps."""

    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = {"from_attributes": True}


class UUIDModel(BaseModel):
    """Base model with UUID primary key."""

    id: UUID = Field(..., description="UUID identifier")

    model_config = {"from_attributes": True}
