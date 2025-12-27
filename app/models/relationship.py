"""
Relationship models matching the relationships schema in init.sql.
Knowledge graph for connecting entities.
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    ForeignKey,
    DateTime,
    CheckConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from pgvector.sqlalchemy import Vector

from app.core.database import Base


class Relationship(Base):
    """
    Relationship model for connecting entities in the knowledge graph.
    Schema: relationships.relationships
    """

    __tablename__ = "relationships"
    __table_args__ = (
        CheckConstraint(
            "from_type IN ('email', 'task', 'calendar', 'document')",
            name="check_from_type",
        ),
        CheckConstraint(
            "to_type IN ('email', 'task', 'calendar', 'document')",
            name="check_to_type",
        ),
        CheckConstraint(
            "created_by IN ('user', 'agent')", name="check_relationship_created_by"
        ),
        CheckConstraint(
            "strength >= 0 AND strength <= 1", name="check_strength_range"
        ),
        Index("idx_relationships_user", "user_id"),
        Index("idx_relationships_from", "from_type", "from_id"),
        Index("idx_relationships_to", "to_type", "to_id"),
        Index("idx_relationships_strength", "strength"),
        {"schema": "relationships"},
    )

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        ForeignKey("users.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_type: Mapped[str] = Column(String(20), nullable=False)
    from_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), nullable=False)
    to_type: Mapped[str] = Column(String(20), nullable=False)
    to_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), nullable=False)
    relationship_type: Mapped[str] = Column(String(50), nullable=False)
    strength: Mapped[float] = Column(Float, default=1.0, nullable=False)
    created_by: Mapped[str] = Column(String(10), default="agent", nullable=False)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<Relationship(id={self.id}, {self.from_type}:{self.from_id} -> {self.to_type}:{self.to_id}, type={self.relationship_type})>"


class EntityEmbedding(Base):
    """
    Entity embedding model for semantic search across different entity types.
    Schema: relationships.entity_embeddings
    """

    __tablename__ = "entity_embeddings"
    __table_args__ = (
        CheckConstraint(
            "entity_type IN ('email', 'task', 'calendar', 'document')",
            name="check_entity_type",
        ),
        Index("idx_entity_embeddings_type", "entity_type", "entity_id"),
        {"schema": "relationships"},
    )

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        ForeignKey("users.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_type: Mapped[str] = Column(String(20), nullable=False)
    entity_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), nullable=False)
    embedding: Mapped[Optional[List[float]]] = Column(Vector(1536), nullable=True)
    text_content: Mapped[Optional[str]] = Column(Text, nullable=True)
    updated_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<EntityEmbedding(id={self.id}, entity_type={self.entity_type}, entity_id={self.entity_id})>"
