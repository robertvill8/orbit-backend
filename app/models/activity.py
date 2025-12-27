"""
Activity model matching the activities schema in init.sql.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped

from app.core.database import Base


class Activity(Base):
    """
    Activity log model for immutable event tracking.
    Schema: activities.activities
    """

    __tablename__ = "activities"
    __table_args__ = (
        Index("idx_activities_user", "user_id", "created_at"),
        Index("idx_activities_type", "action_type"),
        Index("idx_activities_entity", "entity_type", "entity_id"),
        {"schema": "activities"},
    )

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        ForeignKey("users.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    action_type: Mapped[str] = Column(String(50), nullable=False)
    description: Mapped[str] = Column(Text, nullable=False)
    entity_type: Mapped[Optional[str]] = Column(String(20), nullable=True)
    entity_id: Mapped[Optional[uuid.UUID]] = Column(UUID(as_uuid=True), nullable=True)
    meta_data: Mapped[Dict[str, Any]] = Column("metadata", JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<Activity(id={self.id}, type={self.action_type})>"
