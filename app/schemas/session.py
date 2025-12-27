"""
Pydantic schemas for session management.
Defines session creation, retrieval, and update models.
"""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import UUIDModel, TimestampMixin


class SessionCreate(BaseModel):
    """Request schema for creating a new session."""

    device_info: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Device information (platform, browser, etc.)"
    )
    context_data: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Initial context data for the session"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "device_info": {
                    "platform": "web",
                    "browser": "Chrome 120",
                    "user_agent": "Mozilla/5.0..."
                },
                "context_data": {
                    "initial_context": "User wants to check emails"
                }
            }
        }


class SessionUpdate(BaseModel):
    """Request schema for updating session data."""

    context_data: Optional[Dict[str, Any]] = Field(
        None, description="Updated context data"
    )
    extend_ttl: bool = Field(
        False, description="Whether to extend session expiration by another 24 hours"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "context_data": {
                    "user_preference_voice_speed": 1.2
                },
                "extend_ttl": True
            }
        }


class SessionResponse(UUIDModel, TimestampMixin):
    """Response schema for session data."""

    session_id: UUID = Field(..., description="Session unique identifier", alias="id")
    user_id: UUID = Field(..., description="User ID who owns this session")
    device_info: Dict[str, Any] = Field(
        default_factory=dict, description="Device information"
    )
    context_data: Dict[str, Any] = Field(
        default_factory=dict, description="Session context data"
    )
    message_count: int = Field(0, description="Number of messages in this session")
    last_activity_at: datetime = Field(..., description="Last activity timestamp")
    expires_at: datetime = Field(..., description="Session expiration time")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "7f3e5b12-9c7a-4d6e-8f5c-2a1b3c4d5e6f",
                "session_id": "7f3e5b12-9c7a-4d6e-8f5c-2a1b3c4d5e6f",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "device_info": {
                    "platform": "web",
                    "browser": "Chrome 120"
                },
                "context_data": {
                    "conversation_summary": "User checked emails and created 2 tasks",
                    "last_intent": "create_calendar_event"
                },
                "message_count": 15,
                "last_activity_at": "2025-12-10T15:45:00Z",
                "expires_at": "2025-12-11T14:30:00Z",
                "created_at": "2025-12-10T14:30:00Z"
            }
        }

        populate_by_name = True
