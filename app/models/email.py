"""
Email models matching the emails schema in init.sql.
"""

import uuid
from datetime import datetime
from typing import Optional, List

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
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, Mapped

from app.core.database import Base


class Email(Base):
    """
    Email model for storing synchronized email messages.
    Schema: emails.emails
    """

    __tablename__ = "emails"
    __table_args__ = (
        Index("idx_emails_user", "user_id"),
        Index("idx_emails_thread", "thread_id"),
        Index("idx_emails_date", "date"),
        Index("idx_emails_folder", "folder"),
        {"schema": "emails"},
    )

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        ForeignKey("users.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    message_id: Mapped[str] = Column(String(255), unique=True, nullable=False)
    thread_id: Mapped[Optional[str]] = Column(String(255), nullable=True)
    subject: Mapped[Optional[str]] = Column(Text, nullable=True)
    from_email: Mapped[str] = Column(String(255), nullable=False)
    from_name: Mapped[Optional[str]] = Column(String(255), nullable=True)
    to_emails: Mapped[List[str]] = Column(ARRAY(Text), nullable=True)
    cc_emails: Mapped[List[str]] = Column(ARRAY(Text), nullable=True)
    bcc_emails: Mapped[List[str]] = Column(ARRAY(Text), nullable=True)
    body_text: Mapped[Optional[str]] = Column(Text, nullable=True)
    body_html: Mapped[Optional[str]] = Column(Text, nullable=True)
    has_attachments: Mapped[bool] = Column(Boolean, default=False, nullable=False)
    is_read: Mapped[bool] = Column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = Column(Boolean, default=False, nullable=False)
    folder: Mapped[str] = Column(String(100), default="INBOX", nullable=False)
    date: Mapped[datetime] = Column(DateTime(timezone=True), nullable=False)
    synced_at: Mapped[datetime] = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    attachments: Mapped[List["EmailAttachment"]] = relationship(
        "EmailAttachment", back_populates="email", cascade="all, delete-orphan"
    )
    drafts: Mapped[List["EmailDraft"]] = relationship(
        "EmailDraft", back_populates="reply_to_email", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Email(id={self.id}, subject={self.subject}, from={self.from_email})>"


class EmailAttachment(Base):
    """
    Email attachment model.
    Schema: emails.email_attachments
    """

    __tablename__ = "email_attachments"
    __table_args__ = (
        Index("idx_attachments_email", "email_id"),
        {"schema": "emails"},
    )

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        ForeignKey("emails.emails.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_id: Mapped[Optional[uuid.UUID]] = Column(
        UUID(as_uuid=True), nullable=True
    )
    filename: Mapped[str] = Column(String(255), nullable=False)
    content_type: Mapped[Optional[str]] = Column(String(100), nullable=True)
    size_bytes: Mapped[Optional[int]] = Column(Integer, nullable=True)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    email: Mapped["Email"] = relationship("Email", back_populates="attachments")

    def __repr__(self) -> str:
        return f"<EmailAttachment(id={self.id}, filename={self.filename})>"


class EmailDraft(Base):
    """
    Email draft model for agent-generated or user-created draft emails.
    Schema: emails.email_drafts
    """

    __tablename__ = "email_drafts"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'sent', 'discarded')",
            name="check_draft_status"
        ),
        CheckConstraint(
            "created_by IN ('user', 'agent')",
            name="check_draft_created_by"
        ),
        Index("idx_drafts_user", "user_id"),
        Index("idx_drafts_status", "status"),
        {"schema": "emails"},
    )

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        ForeignKey("users.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    reply_to_email_id: Mapped[Optional[uuid.UUID]] = Column(
        UUID(as_uuid=True),
        ForeignKey("emails.emails.id", ondelete="SET NULL"),
        nullable=True,
    )
    to_emails: Mapped[List[str]] = Column(ARRAY(Text), nullable=False)
    cc_emails: Mapped[List[str]] = Column(ARRAY(Text), nullable=True)
    bcc_emails: Mapped[List[str]] = Column(ARRAY(Text), nullable=True)
    subject: Mapped[str] = Column(Text, nullable=False)
    body: Mapped[str] = Column(Text, nullable=False)
    status: Mapped[str] = Column(String(20), default="pending", nullable=False)
    created_by: Mapped[str] = Column(String(10), default="user", nullable=False)
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
    reply_to_email: Mapped[Optional["Email"]] = relationship(
        "Email", back_populates="drafts",
)

    def __repr__(self) -> str:
        return f"<EmailDraft(id={self.id}, subject={self.subject}, status={self.status})>"
