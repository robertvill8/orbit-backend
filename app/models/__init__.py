"""
SQLAlchemy models package.
Import all models here for Alembic autogenerate to detect them.
"""

from app.models.user import User
from app.models.session import Session
from app.models.message import Message, LLMRequest
from app.models.task import Task, TaskTag, TaskList, TaskLabel
from app.models.activity import Activity
from app.models.integration import IntegrationLog
from app.models.email import Email, EmailAttachment, EmailDraft
from app.models.calendar import CalendarEvent, CalendarInvitation
from app.models.document import Document, DocumentTag, DocumentTagAssignment
from app.models.relationship import Relationship, EntityEmbedding

__all__ = [
    # User and session
    "User",
    "Session",
    # Messages
    "Message",
    "LLMRequest",
    # Tasks
    "Task",
    "TaskTag",
    "TaskList",
    "TaskLabel",
    # Activity
    "Activity",
    # Integration
    "IntegrationLog",
    # Email
    "Email",
    "EmailAttachment",
    "EmailDraft",
    # Calendar
    "CalendarEvent",
    "CalendarInvitation",
    # Documents
    "Document",
    "DocumentTag",
    "DocumentTagAssignment",
    # Relationships
    "Relationship",
    "EntityEmbedding",
]
