"""
Activity service for logging system events.
Provides immutable append-only audit trail.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.models.activity import Activity

logger = get_logger(__name__)


class ActivityService:
    """
    Service for activity logging and retrieval.

    Activities are immutable (append-only) events that track:
    - Agent actions (task_created, email_read, calendar_event_created)
    - User actions (manual task creation, etc.)
    - System events (integration_executed, error_occurred)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_activity(
        self,
        user_id: UUID,
        activity_type: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[UUID] = None,
        related_task_id: Optional[UUID] = None,
        related_message_id: Optional[UUID] = None,
    ) -> Activity:
        """
        Log a new activity event.

        Args:
            user_id: User ID
            activity_type: Type of activity (e.g., 'task_created', 'email_searched')
            description: Human-readable description
            metadata: Structured metadata (tool parameters, execution results)
            session_id: Optional session ID
            related_task_id: Optional related task ID
            related_message_id: Optional related message ID

        Returns:
            Created activity instance
        """
        activity = Activity(
            user_id=user_id,
            session_id=session_id,
            activity_type=activity_type,
            description=description,
            metadata=metadata or {},
            related_task_id=related_task_id,
            related_message_id=related_message_id,
        )

        self.db.add(activity)
        await self.db.commit()
        await self.db.refresh(activity)

        logger.info(
            "activity_logged",
            activity_id=activity.id,
            activity_type=activity_type,
            user_id=user_id,
        )

        return activity

    async def get_activities(
        self,
        user_id: UUID,
        activity_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Activity]:
        """
        Retrieve activities for a user.

        Args:
            user_id: User ID
            activity_type: Optional filter by activity type
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of activities
        """
        query = select(Activity).where(Activity.user_id == user_id)

        if activity_type:
            query = query.where(Activity.activity_type == activity_type)

        query = query.order_by(Activity.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_activity(
        self,
        activity_id: UUID,
        user_id: UUID,
    ) -> Optional[Activity]:
        """
        Get single activity by ID.

        Args:
            activity_id: Activity ID
            user_id: User ID (for authorization)

        Returns:
            Activity instance or None
        """
        result = await self.db.execute(
            select(Activity).where(
                Activity.id == activity_id,
                Activity.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_task_activities(
        self,
        task_id: UUID,
        user_id: UUID,
    ) -> List[Activity]:
        """
        Get all activities related to a specific task.

        Args:
            task_id: Task ID
            user_id: User ID (for authorization)

        Returns:
            List of activities related to the task
        """
        result = await self.db.execute(
            select(Activity)
            .where(
                Activity.related_task_id == task_id,
                Activity.user_id == user_id,
            )
            .order_by(Activity.created_at.desc())
        )
        return list(result.scalars().all())
