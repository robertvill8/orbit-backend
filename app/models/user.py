"""
User model matching the users schema in init.sql.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped

from app.core.database import Base


class User(Base):
    """
    User model for authentication and user data.
    Schema: users.users
    """

    __tablename__ = "users"
    __table_args__ = (
        Index("idx_users_email", "email"),
        {"schema": "users"}
    )

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = Column(String(255), unique=True, nullable=False)
    name: Mapped[Optional[str]] = Column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = Column(String, nullable=True)
    preferences: Mapped[Dict[str, Any]] = Column(JSONB, default=dict, nullable=False)
    imap_config: Mapped[Optional[Dict[str, Any]]] = Column(JSONB, nullable=True)
    smtp_config: Mapped[Optional[Dict[str, Any]]] = Column(JSONB, nullable=True)
    caldav_config: Mapped[Optional[Dict[str, Any]]] = Column(JSONB, nullable=True)

    # Authentication field (not in init.sql but needed for auth)
    hashed_password: Mapped[Optional[str]] = Column(String(255), nullable=True)

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
    sessions: Mapped[List["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
