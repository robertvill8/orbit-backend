"""
Notification service for creating and managing user notifications.
Handles notification persistence and WebSocket delivery.
"""
from datetime import datetime, UTC
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationResponse, NotificationListResponse

if TYPE_CHECKING:
    from app.services.websocket.manager import WebSocketManager

logger = get_logger(__name__)


class NotificationService:
    """
    Service for managing user notifications.

    Features:
    - Create and store notifications in database
    - Push notifications via WebSocket to active sessions
    - Retrieve notifications with filtering and pagination
    - Mark notifications as read/unread
    - Delete notifications

    Args:
        db: SQLAlchemy async session
        ws_manager: Optional WebSocket manager for real-time push
    """

    def __init__(self, db: AsyncSession, ws_manager: Optional["WebSocketManager"] = None):
        """
        Initialize notification service.

        Args:
            db: Database session
            ws_manager: Optional WebSocket manager for real-time delivery
        """
        self.db = db
        self.ws_manager = ws_manager

    async def create_notification(
        self,
        notification_data: NotificationCreate,
        send_websocket: bool = True,
    ) -> NotificationResponse:
        """
        Create a new notification and optionally send via WebSocket.

        Args:
            notification_data: Notification creation data
            send_websocket: Whether to push via WebSocket (default: True)

        Returns:
            Created notification

        Workflow:
            1. Create notification in database
            2. If WebSocket manager available and send_websocket=True:
               - Send notification to user's active sessions
            3. Return notification response

        Example:
            notification = await service.create_notification(
                NotificationCreate(
                    user_id=user_id,
                    title="New Task",
                    content="Task created from email",
                    type="task_created",
                    related_entity_type="task",
                    related_entity_id=task_id
                )
            )
        """
        # Create notification model
        notification = Notification(
            user_id=notification_data.user_id,
            title=notification_data.title,
            content=notification_data.content,
            type=notification_data.type,
            action=notification_data.action,
            related_entity_type=notification_data.related_entity_type,
            related_entity_id=notification_data.related_entity_id,
            is_read=False,
        )

        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)

        logger.info(
            "notification_created",
            notification_id=str(notification.id),
            user_id=str(notification_data.user_id),
            type=notification_data.type,
        )

        # Send via WebSocket if manager available
        if self.ws_manager and send_websocket:
            try:
                await self._send_websocket_notification(notification)
            except Exception as e:
                logger.error(
                    "websocket_notification_failed",
                    notification_id=str(notification.id),
                    error=str(e),
                )
                # Don't fail the whole operation if WebSocket send fails

        return NotificationResponse(
            id=notification.id,
            user_id=notification.user_id,
            title=notification.title,
            content=notification.content,
            type=notification.type,
            action=notification.action,
            related_entity_type=notification.related_entity_type,
            related_entity_id=notification.related_entity_id,
            is_read=notification.is_read,
            read_at=notification.read_at,
            created_at=notification.created_at,
            updated_at=notification.updated_at,
        )

    async def _send_websocket_notification(self, notification: Notification) -> None:
        """
        Send notification to user via WebSocket.

        Args:
            notification: Notification model to send
        """
        if not self.ws_manager:
            return

        message = {
            "type": "notification",
            "data": {
                "id": str(notification.id),
                "title": notification.title,
                "content": notification.content,
                "notification_type": notification.type,
                "action": notification.action,
                "related_entity_type": notification.related_entity_type,
                "related_entity_id": str(notification.related_entity_id) if notification.related_entity_id else None,
                "created_at": notification.created_at.isoformat(),
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Send to all user's active sessions
        sent_count = await self.ws_manager.send_to_user(notification.user_id, message)

        logger.debug(
            "notification_sent_via_websocket",
            notification_id=str(notification.id),
            user_id=str(notification.user_id),
            sent_count=sent_count,
        )

    async def get_notifications(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        unread_only: bool = False,
        notification_type: Optional[str] = None,
    ) -> NotificationListResponse:
        """
        Get paginated list of notifications for a user.

        Args:
            user_id: User ID to fetch notifications for
            page: Page number (1-indexed)
            page_size: Number of items per page
            unread_only: Filter to unread notifications only
            notification_type: Optional filter by notification type

        Returns:
            Paginated notification list with metadata

        Example:
            response = await service.get_notifications(
                user_id=user_id,
                page=1,
                page_size=20,
                unread_only=True
            )
        """
        # Build query filters
        filters = [Notification.user_id == user_id]

        if unread_only:
            filters.append(Notification.is_read == False)

        if notification_type:
            filters.append(Notification.type == notification_type)

        # Get total count
        count_query = select(func.count()).select_from(Notification).where(and_(*filters))
        total_count = await self.db.scalar(count_query) or 0

        # Get unread count
        unread_query = (
            select(func.count())
            .select_from(Notification)
            .where(and_(Notification.user_id == user_id, Notification.is_read == False))
        )
        unread_count = await self.db.scalar(unread_query) or 0

        # Get paginated notifications
        offset = (page - 1) * page_size
        query = (
            select(Notification)
            .where(and_(*filters))
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        notifications = result.scalars().all()

        # Convert to response models
        notification_responses = [
            NotificationResponse(
                id=n.id,
                user_id=n.user_id,
                title=n.title,
                content=n.content,
                type=n.type,
                action=n.action,
                related_entity_type=n.related_entity_type,
                related_entity_id=n.related_entity_id,
                is_read=n.is_read,
                read_at=n.read_at,
                created_at=n.created_at,
                updated_at=n.updated_at,
            )
            for n in notifications
        ]

        has_next = (offset + page_size) < total_count

        return NotificationListResponse(
            notifications=notification_responses,
            total_count=total_count,
            unread_count=unread_count,
            page=page,
            page_size=page_size,
            has_next=has_next,
        )

    async def mark_as_read(self, notification_id: UUID, user_id: UUID) -> Optional[NotificationResponse]:
        """
        Mark a notification as read.

        Args:
            notification_id: Notification ID
            user_id: User ID (for authorization)

        Returns:
            Updated notification or None if not found

        Raises:
            PermissionError: If user doesn't own the notification
        """
        result = await self.db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one_or_none()

        if not notification:
            return None

        # Authorization check
        if notification.user_id != user_id:
            raise PermissionError("User does not own this notification")

        # Mark as read
        notification.mark_as_read()
        await self.db.commit()
        await self.db.refresh(notification)

        logger.info(
            "notification_marked_read",
            notification_id=str(notification_id),
            user_id=str(user_id),
        )

        return NotificationResponse(
            id=notification.id,
            user_id=notification.user_id,
            title=notification.title,
            content=notification.content,
            type=notification.type,
            action=notification.action,
            related_entity_type=notification.related_entity_type,
            related_entity_id=notification.related_entity_id,
            is_read=notification.is_read,
            read_at=notification.read_at,
            created_at=notification.created_at,
            updated_at=notification.updated_at,
        )

    async def mark_all_as_read(self, user_id: UUID) -> int:
        """
        Mark all unread notifications as read for a user.

        Args:
            user_id: User ID

        Returns:
            Number of notifications marked as read
        """
        from sqlalchemy import update

        result = await self.db.execute(
            update(Notification)
            .where(and_(Notification.user_id == user_id, Notification.is_read == False))
            .values(is_read=True, read_at=datetime.now(UTC))
        )

        await self.db.commit()

        count = result.rowcount or 0

        logger.info(
            "notifications_marked_all_read",
            user_id=str(user_id),
            count=count,
        )

        return count

    async def delete_notification(self, notification_id: UUID, user_id: UUID) -> bool:
        """
        Delete a notification.

        Args:
            notification_id: Notification ID
            user_id: User ID (for authorization)

        Returns:
            True if deleted, False if not found

        Raises:
            PermissionError: If user doesn't own the notification
        """
        from sqlalchemy import delete

        result = await self.db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one_or_none()

        if not notification:
            return False

        # Authorization check
        if notification.user_id != user_id:
            raise PermissionError("User does not own this notification")

        await self.db.execute(
            delete(Notification).where(Notification.id == notification_id)
        )
        await self.db.commit()

        logger.info(
            "notification_deleted",
            notification_id=str(notification_id),
            user_id=str(user_id),
        )

        return True
