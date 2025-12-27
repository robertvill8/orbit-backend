"""
Document models matching the documents schema in init.sql.
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    ForeignKey,
    DateTime,
    CheckConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
from pgvector.sqlalchemy import Vector

from app.core.database import Base


class Document(Base):
    """
    Document model for uploaded files with OCR and embeddings.
    Schema: documents.documents
    """

    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint(
            "processing_status IN ('queued', 'processing', 'complete', 'failed')",
            name="check_processing_status",
        ),
        Index("idx_documents_user", "user_id"),
        Index("idx_documents_type", "file_type"),
        Index("idx_documents_status", "processing_status"),
        {"schema": "documents"},
    )

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        ForeignKey("users.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    filename: Mapped[str] = Column(String(255), nullable=False)
    storage_path: Mapped[str] = Column(Text, nullable=False)
    file_type: Mapped[str] = Column(String(50), nullable=False)
    size_bytes: Mapped[int] = Column(Integer, nullable=False)
    extracted_text: Mapped[Optional[str]] = Column(Text, nullable=True)
    summary_short: Mapped[Optional[str]] = Column(Text, nullable=True)
    summary_medium: Mapped[Optional[str]] = Column(Text, nullable=True)
    summary_long: Mapped[Optional[str]] = Column(Text, nullable=True)
    embedding: Mapped[Optional[List[float]]] = Column(Vector(1536), nullable=True)
    processing_status: Mapped[str] = Column(
        String(20), default="queued", nullable=False
    )
    processing_error: Mapped[Optional[str]] = Column(Text, nullable=True)
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
    tag_assignments: Mapped[List["DocumentTagAssignment"]] = relationship(
        "DocumentTagAssignment",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename}, status={self.processing_status})>"


class DocumentTag(Base):
    """
    Document tag model for categorizing documents.
    Schema: documents.document_tags
    """

    __tablename__ = "document_tags"
    __table_args__ = (
        Index("idx_doc_tags_user", "user_id"),
        {"schema": "documents"},
    )

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        ForeignKey("users.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = Column(String(50), nullable=False)
    color: Mapped[str] = Column(String(7), nullable=False)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    document_assignments: Mapped[List["DocumentTagAssignment"]] = relationship(
        "DocumentTagAssignment", back_populates="tag", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<DocumentTag(id={self.id}, name={self.name})>"


class DocumentTagAssignment(Base):
    """
    Many-to-many relationship between documents and tags.
    Schema: documents.document_tag_assignments
    """

    __tablename__ = "document_tag_assignments"
    __table_args__ = (
        Index("idx_doc_tags_doc", "document_id"),
        Index("idx_doc_tags_tag", "tag_id"),
        {"schema": "documents"},
    )

    document_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.documents.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.document_tags.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Relationships
    document: Mapped["Document"] = relationship(
        "Document", back_populates="tag_assignments"
    )
    tag: Mapped["DocumentTag"] = relationship(
        "DocumentTag", back_populates="document_assignments",
)

    def __repr__(self) -> str:
        return f"<DocumentTagAssignment(document_id={self.document_id}, tag_id={self.tag_id})>"
