"""
Message and LLM request models matching the messages schema in init.sql.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    CheckConstraint,
    Index,
    DECIMAL,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped

from app.core.database import Base


class Message(Base):
    """
    Message model for conversation history.
    Schema: messages.messages
    """

    __tablename__ = "messages"
    __table_args__ = (
                CheckConstraint("role IN ('user', 'assistant')", name="check_message_role"),
        CheckConstraint(
            "message_type IN ('text', 'audio')", name="check_message_type"
        ),
        Index("idx_messages_session", "session_id"),
        Index("idx_messages_created", "created_at"),
        {"schema": "messages"},
    )

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = Column(String(20), nullable=False)
    content: Mapped[str] = Column(Text, nullable=False)
    message_type: Mapped[str] = Column(String(20), nullable=False)
    audio_url: Mapped[Optional[str]] = Column(Text, nullable=True)
    meta_data: Mapped[Dict[str, Any]] = Column("metadata", JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role}, type={self.message_type})>"


class LLMRequest(Base):
    """
    LLM API request log for cost tracking and debugging.
    Schema: messages.llm_requests
    """

    __tablename__ = "llm_requests"
    __table_args__ = (
        Index("idx_llm_requests_user", "user_id", "created_at"),
        Index("idx_llm_requests_created", "created_at"),
        {"schema": "messages"},
    )

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    message_id: Mapped[Optional[uuid.UUID]] = Column(
        UUID(as_uuid=True),
        ForeignKey("messages.messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        ForeignKey("users.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    model: Mapped[str] = Column(String(100), nullable=False)
    input_tokens: Mapped[int] = Column(Integer, nullable=False)
    output_tokens: Mapped[int] = Column(Integer, nullable=False)
    total_cost: Mapped[Optional[Decimal]] = Column(DECIMAL(10, 6), nullable=True)
    latency_ms: Mapped[Optional[int]] = Column(Integer, nullable=True)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<LLMRequest(id={self.id}, model={self.model}, tokens={self.input_tokens + self.output_tokens})>"
