#!/usr/bin/env python3
"""
Script to generate complete backend project structure with all files.
This ensures consistency and completeness across all modules.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent


def create_file(filepath: str, content: str) -> None:
    """Create a file with given content, creating parent directories if needed."""
    file_path = BASE_DIR / filepath
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        f.write(content)
    print(f"Created: {filepath}")


# Generate all model files
MODELS = {
    "app/models/session.py": '''"""Session model."""
import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Session(Base):
    """Session model for conversation management."""

    __tablename__ = "sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    device_info = Column(JSON, default=dict, nullable=False)
    context_data = Column(JSON, default=dict, nullable=False)
    last_activity_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.utcnow() + timedelta(hours=24),
        nullable=False
    )
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="session")
    activities = relationship("Activity", back_populates="session")

    def __repr__(self) -> str:
        return f"<Session(session_id={self.session_id}, user_id={self.user_id})>"
''',

    "app/models/message.py": '''"""Message and LLM request models."""
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Message(Base):
    """Message model for conversation history."""

    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default="text", nullable=False)
    metadata = Column(JSON, default=dict, nullable=False)
    token_count = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'system')", name="check_message_role"),
        CheckConstraint("content_type IN ('text', 'audio', 'image')", name="check_content_type"),
    )

    # Relationships
    session = relationship("Session", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role}, session_id={self.session_id})>"


class LLMRequest(Base):
    """LLM API request log for debugging and cost tracking."""

    __tablename__ = "llm_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.session_id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    provider = Column(String(50), nullable=False, index=True)
    model_name = Column(String(100), nullable=False)
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)
    estimated_cost_usd = Column(String(20), nullable=True)
    latency_ms = Column(Integer, nullable=True)
    request_payload = Column(JSON, nullable=True)
    response_payload = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<LLMRequest(id={self.id}, provider={self.provider}, model={self.model_name})>"
''',

    "app/models/task.py": '''"""Task models."""
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Task(Base):
    """Task model for user tasks."""

    __tablename__ = "tasks"
    __table_args__ = (
        {"schema": "tasks"},
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', 'archived', 'cancelled')",
            name="check_task_status"
        ),
        CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'urgent')",
            name="check_task_priority"
        ),
        CheckConstraint(
            "created_by IN ('user', 'agent')",
            name="check_created_by"
        ),
        CheckConstraint(
            "(status = 'completed' AND completed_at IS NOT NULL) OR (status != 'completed')",
            name="check_completed_at"
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.session_id", ondelete="SET NULL"),
        nullable=True
    )
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="pending", nullable=False, index=True)
    priority = Column(String(20), default="medium", nullable=False, index=True)
    due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(50), default="agent", nullable=False)
    source_message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True
    )
    metadata = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="tasks")
    session = relationship("Session", back_populates="tasks")
    tags = relationship("TaskTag", back_populates="task", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="related_task")

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title={self.title}, status={self.status})>"


class TaskTag(Base):
    """Task tag model (many-to-many)."""

    __tablename__ = "task_tags"
    __table_args__ = {"schema": "tasks"}

    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tasks.tasks.id", ondelete="CASCADE"),
        primary_key=True
    )
    tag_name = Column(String(100), primary_key=True, index=True)

    # Relationships
    task = relationship("Task", back_populates="tags")

    def __repr__(self) -> str:
        return f"<TaskTag(task_id={self.task_id}, tag={self.tag_name})>"
''',

    "app/models/activity.py": '''"""Activity model."""
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Activity(Base):
    """Activity log model (immutable event log)."""

    __tablename__ = "activities"
    __table_args__ = {"schema": "activities"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.session_id", ondelete="SET NULL"),
        nullable=True
    )
    activity_type = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    metadata = Column(JSON, default=dict, nullable=False)
    related_task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tasks.tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    related_message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True
    )
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="activities")
    session = relationship("Session", back_populates="activities")
    related_task = relationship("Task", back_populates="activities")

    def __repr__(self) -> str:
        return f"<Activity(id={self.id}, type={self.activity_type})>"
''',

    "app/models/integration.py": '''"""Integration log model."""
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class IntegrationLog(Base):
    """Integration API call log model."""

    __tablename__ = "integration_logs"
    __table_args__ = {"schema": "integrations"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.session_id", ondelete="SET NULL"),
        nullable=True
    )
    integration_name = Column(String(100), nullable=False, index=True)
    workflow_id = Column(String(255), nullable=True)
    request_method = Column(String(10), nullable=False)
    request_url = Column(Text, nullable=False)
    request_payload = Column(JSON, nullable=True)
    response_status = Column(Integer, nullable=True, index=True)
    response_payload = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<IntegrationLog(id={self.id}, integration={self.integration_name})>"
''',
}

# Create all model files
for filepath, content in MODELS.items():
    create_file(filepath, content)

print("\n✅ All database models generated successfully!")
print("\nNext steps:")
print("1. Create Pydantic schemas in app/schemas/")
print("2. Implement service layer in app/services/")
print("3. Create API routers in app/api/v1/routes/")
print("4. Implement main.py FastAPI application")
print("5. Set up Alembic migrations")
print("6. Write comprehensive tests")
