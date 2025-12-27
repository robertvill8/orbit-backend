"""
Task Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.schemas.common import UUIDModel, TimestampMixin


class TaskListBase(BaseModel):
    """Base TaskList schema."""

    name: str = Field(..., max_length=100, description="List name")
    position: int = Field(..., ge=0, description="Position in Kanban board")
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$", description="Hex color code")


class TaskListCreate(TaskListBase):
    """TaskList creation schema."""

    pass


class TaskListUpdate(BaseModel):
    """TaskList update schema."""

    name: Optional[str] = Field(None, max_length=100)
    position: Optional[int] = Field(None, ge=0)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")


class TaskListResponse(TaskListBase, UUIDModel, TimestampMixin):
    """TaskList response schema."""

    user_id: UUID

    model_config = {"from_attributes": True}


class TaskBase(BaseModel):
    """Base Task schema."""

    title: str = Field(..., max_length=500, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")
    status: str = Field(
        default="open",
        pattern="^(backlog|open|in_progress|waiting|done|pending|dismissed)$",
    )
    due_date: Optional[datetime] = Field(None, description="Task due date")


class TaskCreate(TaskBase):
    """Task creation schema."""

    list_id: UUID = Field(..., description="Parent list ID")
    parent_id: Optional[UUID] = Field(None, description="Parent task ID for subtasks")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")


class TaskUpdate(BaseModel):
    """Task update schema."""

    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None)
    priority: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    status: Optional[str] = Field(
        None, pattern="^(backlog|open|in_progress|waiting|done|pending|dismissed)$"
    )
    due_date: Optional[datetime] = None
    list_id: Optional[UUID] = None
    vertical_position: Optional[int] = Field(None, ge=0)


class TaskResponse(TaskBase, UUIDModel, TimestampMixin):
    """Task response schema."""

    user_id: UUID
    list_id: UUID
    parent_id: Optional[UUID]
    vertical_position: int
    created_by: str
    extracted_from: Optional[str]
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class TaskLabelBase(BaseModel):
    """Base TaskLabel schema."""

    name: str = Field(..., max_length=50, description="Label name")
    color: str = Field(..., pattern="^#[0-9A-Fa-f]{6}$", description="Hex color code")


class TaskLabelCreate(TaskLabelBase):
    """TaskLabel creation schema."""

    pass


class TaskLabelResponse(TaskLabelBase, UUIDModel, TimestampMixin):
    """TaskLabel response schema."""

    user_id: UUID

    model_config = {"from_attributes": True}


class TaskWithLabels(TaskResponse):
    """Task response with labels."""

    labels: List[TaskLabelResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class TaskFilters(BaseModel):
    """Filters for task queries."""

    status: Optional[str] = Field(None, pattern="^(backlog|open|in_progress|waiting|done|pending|dismissed)$")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    list_id: Optional[UUID] = None
    due_date_from: Optional[datetime] = None
    due_date_to: Optional[datetime] = None
    search: Optional[str] = Field(None, max_length=200)
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "status": "open",
                "priority": "high",
                "limit": 20,
                "offset": 0
            }
        }
