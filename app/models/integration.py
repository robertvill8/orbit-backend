"""
Integration log model matching the integrations schema in init.sql.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped

from app.core.database import Base


class IntegrationLog(Base):
    """
    Integration log model for n8n workflow tracking.
    Schema: integrations.integration_logs
    """

    __tablename__ = "integration_logs"
    __table_args__ = (
                Index("idx_integration_logs_user", "user_id", "created_at"),
        Index("idx_integration_logs_status", "status"),
        Index("idx_integration_logs_workflow", "workflow_name"),
    )

    id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = Column(
        UUID(as_uuid=True),
        ForeignKey("users.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    workflow_name: Mapped[str] = Column(String(100), nullable=False)
    request_payload: Mapped[Optional[Dict[str, Any]]] = Column(JSONB, nullable=True)
    response_payload: Mapped[Optional[Dict[str, Any]]] = Column(JSONB, nullable=True)
    status: Mapped[Optional[str]] = Column(String(20), nullable=True)
    error_message: Mapped[Optional[str]] = Column(Text, nullable=True)
    latency_ms: Mapped[Optional[int]] = Column(Integer, nullable=True)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False,
)

    def __repr__(self) -> str:
        return f"<IntegrationLog(id={self.id}, workflow={self.workflow_name})>"
