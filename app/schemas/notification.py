"""
Pydantic schemas for notification endpoints.
Defines request/response models for notification management.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import UUIDModel, TimestampMixin


class NotificationAction(BaseModel):
    """Action associated with a notification."""

    type: str = Field(..., description="Action type (e.g., 'open_task', 'view_email')")
    label: str = Field(..., description="Human-readable action label")
    url: Optional[str] = Field(None, description="Optional URL to navigate to")
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="Additional action parameters"
    )


class NotificationBase(BaseModel):
    """Base notification schema with common fields."""

    title: str = Field(..., min_length=1, max_length=255, description="Notification title")
    content: str = Field(..., min_length=1, description="Notification content/message")
    type: str = Field(
        ...,
        description="Notification type (e.g., 'task_created', 'email_received', 'calendar_reminder')"
    )
    action: Optional[Dict[str, Any]] = Field(None, description="Optional action data")
    related_entity_type: Optional[str] = Field(
        None, description="Type of related entity (e.g., 'task', 'email', 'calendar_event')"
    )
    related_entity_id: Optional[UUID] = Field(
        None, description="ID of related entity"
    )


class NotificationCreate(NotificationBase):
    """Schema for creating a new notification."""

    user_id: UUID = Field(..., description="User ID to send notification to")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "New Task Created",
                "content": "Task 'Review tenant application' has been created from your email",
                "type": "task_created",
                "action": {
                    "type": "open_task",
                    "label": "View Task",
                    "url": "/tasks/7f3e5b12-9c7a-4d6e-8f5c-2a1b3c4d5e6f"
                },
                "related_entity_type": "task",
                "related_entity_id": "7f3e5b12-9c7a-4d6e-8f5c-2a1b3c4d5e6f"
            }
        }


class NotificationUpdate(BaseModel):
    """Schema for updating a notification."""

    is_read: Optional[bool] = Field(None, description="Mark as read/unread")


class NotificationResponse(UUIDModel, NotificationBase, TimestampMixin):
    """Response schema for notification data."""

    user_id: UUID = Field(..., description="User ID who owns this notification")
    is_read: bool = Field(..., description="Read status")
    read_at: Optional[datetime] = Field(None, description="Timestamp when marked as read")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "7f3e5b12-9c7a-4d6e-8f5c-2a1b3c4d5e6f",
                "title": "New Task Created",
                "content": "Task 'Review tenant application' has been created from your email",
                "type": "task_created",
                "action": {
                    "type": "open_task",
                    "label": "View Task",
                    "url": "/tasks/abc-123"
                },
                "related_entity_type": "task",
                "related_entity_id": "abc-123-def-456",
                "is_read": False,
                "read_at": None,
                "created_at": "2025-12-10T14:30:00Z",
                "updated_at": "2025-12-10T14:30:00Z"
            }
        }


class NotificationListResponse(BaseModel):
    """Response schema for notification list with pagination."""

    notifications: List[NotificationResponse] = Field(..., description="List of notifications")
    total_count: int = Field(..., description="Total number of notifications")
    unread_count: int = Field(..., description="Number of unread notifications")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    has_next: bool = Field(..., description="Whether there are more pages")

    class Config:
        json_schema_extra = {
            "example": {
                "notifications": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "user_id": "7f3e5b12-9c7a-4d6e-8f5c-2a1b3c4d5e6f",
                        "title": "New Task Created",
                        "content": "Task created from email",
                        "type": "task_created",
                        "is_read": False,
                        "created_at": "2025-12-10T14:30:00Z"
                    }
                ],
                "total_count": 42,
                "unread_count": 5,
                "page": 1,
                "page_size": 20,
                "has_next": True
            }
        }


class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages."""

    type: str = Field(..., description="Message type")
    data: Optional[Dict[str, Any]] = Field(None, description="Message payload")
    timestamp: Optional[datetime] = Field(None, description="Message timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "notification",
                "data": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "title": "New Task Created",
                    "content": "Task created from email"
                },
                "timestamp": "2025-12-10T14:30:00Z"
            }
        }
