"""
Calendar models matching the calendar schema in init.sql.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    DateTime,
    Integer,
    ForeignKey,
    CheckConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped

from app.core.database import Base


class CalendarEvent(Base):
    """
    Calendar event model for synchronized calendar entries.
    Schema: calendar.calendar_events
    """

    __tablename__ = "calendar_events"
    __table_args__ = (
        Index("idx_events_user", "user_id"),
        Index("idx_events_start", "start_time"),
        Index("idx_events_range", "user_id", "start_time", "end_time"),
        {"schema": "calendar"},
    )

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        ForeignKey("users.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_id: Mapped[str] = Column(String(255), unique=True, nullable=False)
    title: Mapped[str] = Column(Text, nullable=False)
    description: Mapped[Optional[str]] = Column(Text, nullable=True)
    location: Mapped[Optional[str]] = Column(Text, nullable=True)
    start_time: Mapped[datetime] = Column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = Column(DateTime(timezone=True), nullable=False)
    all_day: Mapped[bool] = Column(Boolean, default=False, nullable=False)
    attendees: Mapped[List[Dict[str, Any]]] = Column(JSONB, default=list, nullable=False)
    recurrence_rule: Mapped[Optional[str]] = Column(Text, nullable=True)
    reminder_minutes: Mapped[Optional[int]] = Column(Integer, nullable=True)
    calendar_color: Mapped[Optional[str]] = Column(String(7), nullable=True)
    synced_at: Mapped[datetime] = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    invitations: Mapped[List["CalendarInvitation"]] = relationship(
        "CalendarInvitation", back_populates="event", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CalendarEvent(id={self.id}, title={self.title}, start={self.start_time})>"


class CalendarInvitation(Base):
    """
    Calendar invitation model for tracking event attendee responses.
    Schema: calendar.calendar_invitations
    """

    __tablename__ = "calendar_invitations"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'accepted', 'declined', 'tentative')",
            name="check_invitation_status",
        ),
        Index("idx_invitations_event", "event_id"),
        {"schema": "calendar"},
    )

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        ForeignKey("calendar.calendar_events.id", ondelete="CASCADE"),
        nullable=False,
    )
    invitee_email: Mapped[str] = Column(String(255), nullable=False)
    status: Mapped[str] = Column(String(20), default="pending", nullable=False)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    event: Mapped["CalendarEvent"] = relationship(
        "CalendarEvent", back_populates="invitations"
    )

    def __repr__(self) -> str:
        return f"<CalendarInvitation(id={self.id}, invitee={self.invitee_email}, status={self.status})>"
