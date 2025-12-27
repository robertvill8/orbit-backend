"""
Task models matching the tasks schema in init.sql.
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    CheckConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped

from app.core.database import Base


class TaskList(Base):
    """
    Task list model for Kanban columns.
    Schema: tasks.task_lists
    """

    __tablename__ = "task_lists"
    __table_args__ = (
        Index("idx_lists_user", "user_id", "position"),
        {"schema": "tasks"},
    )

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        ForeignKey("users.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = Column(String(100), nullable=False)
    position: Mapped[int] = Column(Integer, nullable=False)
    color: Mapped[Optional[str]] = Column(String(7), nullable=True)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    tasks: Mapped[List["Task"]] = relationship(
        "Task", back_populates="task_list", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TaskList(id={self.id}, name={self.name})>"


class Task(Base):
    """
    Task model for user tasks.
    Schema: tasks.tasks
    """

    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "status IN ('backlog', 'open', 'in_progress', 'waiting', 'done', 'pending', 'dismissed')",
            name="check_task_status",
        ),
        CheckConstraint(
            "priority IN ('low', 'medium', 'high')", name="check_task_priority"
        ),
        CheckConstraint(
            "created_by IN ('user', 'agent')", name="check_created_by"
        ),
        Index("idx_tasks_user", "user_id"),
        Index("idx_tasks_list", "list_id", "vertical_position"),
        Index("idx_tasks_status", "status"),
        Index("idx_tasks_parent", "parent_id"),
        Index("idx_tasks_due", "due_date"),
        {"schema": "tasks"},
    )

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        ForeignKey("users.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    list_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        ForeignKey("tasks.task_lists.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_id: Mapped[Optional[uuid.UUID]] = Column(
        UUID(as_uuid=True),
        ForeignKey("tasks.tasks.id", ondelete="CASCADE"),
        nullable=True,
    )
    title: Mapped[str] = Column(Text, nullable=False)
    description: Mapped[Optional[str]] = Column(Text, nullable=True)
    priority: Mapped[str] = Column(String(10), default="medium", nullable=False)
    status: Mapped[str] = Column(String(20), default="open", nullable=False)
    due_date: Mapped[Optional[datetime]] = Column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True), nullable=True
    )
    vertical_position: Mapped[int] = Column(Integer, default=0, nullable=False)
    created_by: Mapped[str] = Column(String(10), default="user", nullable=False)
    extracted_from: Mapped[Optional[str]] = Column(Text, nullable=True)
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
    task_list: Mapped["TaskList"] = relationship("TaskList", back_populates="tasks")
    parent: Mapped[Optional["Task"]] = relationship(
        "Task", remote_side=[id], backref="subtasks"
    )
    tag_assignments: Mapped[List["TaskTag"]] = relationship(
        "TaskTag", back_populates="task", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title={self.title}, status={self.status})>"


class TaskLabel(Base):
    """
    Task label model for categorizing tasks.
    Schema: tasks.task_labels
    """

    __tablename__ = "task_labels"
    __table_args__ = ({"schema": "tasks"},)

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
    task_assignments: Mapped[List["TaskTag"]] = relationship(
        "TaskTag", back_populates="label", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TaskLabel(id={self.id}, name={self.name})>"


class TaskTag(Base):
    """
    Many-to-many relationship between tasks and labels.
    Schema: tasks.task_tags
    """

    __tablename__ = "task_tags"
    __table_args__ = (
        Index("idx_task_tags_task", "task_id"),
        Index("idx_task_tags_label", "label_id"),
        {"schema": "tasks"},
    )

    task_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        ForeignKey("tasks.tasks.id", ondelete="CASCADE"),
        primary_key=True,
    )
    label_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        ForeignKey("tasks.task_labels.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="tag_assignments")
    label: Mapped["TaskLabel"] = relationship(
        "TaskLabel", back_populates="task_assignments",
)

    def __repr__(self) -> str:
        return f"<TaskTag(task_id={self.task_id}, label_id={self.label_id})>"
