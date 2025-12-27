"""
Notification model for proactive user notifications.
Stores notification data for push delivery via WebSocket.
"""
import uuid
from datetime import datetime, UTC
from typing import Dict, Any, Optional

from sqlalchemy import String, Text, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Notification(Base):
    """
    Notification model for proactive user notifications.

    Schema: notifications.notifications

    Notifications are created by the agent or system and pushed to users
    via WebSocket. Users can mark them as read or dismiss them.

    Examples:
        - "New task created: Review property inspection report"
        - "Email received from tenant about maintenance request"
        - "Calendar event starting in 15 minutes"
        - "Document processing completed"
    """

    __tablename__ = "notifications"
    __table_args__ = (
        Index("idx_notifications_user_id", "user_id"),
        Index("idx_notifications_created_at", "created_at"),
        Index("idx_notifications_is_read", "is_read"),
        Index("idx_notifications_type", "type"),
        {"schema": "notifications"},
    )

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Foreign keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.users.id"), nullable=False
    )

    # Notification content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Optional action data (e.g., "open_task", "view_email")
    action: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Related entity reference (task_id, email_id, calendar_event_id, etc.)
    related_entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    related_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Read status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.type}, title={self.title[:30]})>"

    def mark_as_read(self) -> None:
        """Mark notification as read with timestamp."""
        self.is_read = True
        self.read_at = datetime.now(UTC)
