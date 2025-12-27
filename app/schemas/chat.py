"""
Pydantic schemas for chat and agent communication.
Defines request/response models for chat endpoints.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import UUIDModel, TimestampMixin


class ToolCall(BaseModel):
    """Represents a tool call made by the LLM."""

    name: str = Field(..., description="Name of the tool being called")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Parameters passed to the tool"
    )
    result: Optional[Dict[str, Any]] = Field(
        None, description="Result returned from tool execution"
    )


class ChatMessageRequest(BaseModel):
    """Request schema for sending a chat message."""

    message: str = Field(..., min_length=1, max_length=10000, description="User message text")
    session_id: Optional[UUID] = Field(
        None, description="Session ID for conversation context (auto-created if not provided)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Check my emails from today",
                "session_id": "7f3e5b12-9c7a-4d6e-8f5c-2a1b3c4d5e6f"
            }
        }


class ChatMessageResponse(UUIDModel, TimestampMixin):
    """Response schema for chat messages."""

    reply: str = Field(..., description="Assistant's response text")
    session_id: UUID = Field(..., description="Session ID for this conversation")
    tool_calls: Optional[List[ToolCall]] = Field(
        None, description="List of tools called during this interaction"
    )
    tokens_used: Optional[int] = Field(None, description="Total tokens consumed by LLM")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "reply": "I found 3 new emails from today. Would you like me to summarize them?",
                "session_id": "7f3e5b12-9c7a-4d6e-8f5c-2a1b3c4d5e6f",
                "tool_calls": [
                    {
                        "name": "search_email",
                        "parameters": {"query": "today"},
                        "result": {"email_count": 3}
                    }
                ],
                "tokens_used": 450,
                "created_at": "2025-12-10T14:30:00Z"
            }
        }


class VoiceMessageRequest(BaseModel):
    """Request schema for voice message upload."""

    session_id: Optional[UUID] = Field(
        None, description="Session ID for conversation context"
    )
    # File will be handled via FastAPI UploadFile, not in schema


class MessageHistoryResponse(BaseModel):
    """Response schema for message history."""

    session_id: UUID
    messages: List["MessageItem"]
    total_count: int

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "7f3e5b12-9c7a-4d6e-8f5c-2a1b3c4d5e6f",
                "messages": [
                    {
                        "id": "msg-001",
                        "role": "user",
                        "content": "Check my emails",
                        "created_at": "2025-12-10T14:30:00Z"
                    },
                    {
                        "id": "msg-002",
                        "role": "assistant",
                        "content": "I found 3 new emails...",
                        "created_at": "2025-12-10T14:30:05Z"
                    }
                ],
                "total_count": 2
            }
        }


class MessageItem(UUIDModel, TimestampMixin):
    """Individual message in conversation history."""

    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata (tool calls, etc.)"
    )


# Forward reference resolution
MessageHistoryResponse.model_rebuild()
