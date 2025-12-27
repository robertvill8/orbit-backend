"""
REST API endpoints for notification management.
Provides CRUD operations for user notifications.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.services.notification.service import NotificationService
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationListResponse,
    NotificationUpdate,
)
from app.schemas.common import MessageResponse

router = APIRouter()
logger = get_logger(__name__)


def get_notification_service(
    db: AsyncSession = Depends(get_db),
) -> NotificationService:
    """
    Dependency to provide NotificationService with WebSocket manager.

    Note: WebSocket manager is retrieved from app.state in the endpoint.
    """
    # WebSocket manager will be injected separately in endpoints that need it
    return NotificationService(db=db, ws_manager=None)


@router.get("/notifications", response_model=NotificationListResponse)
async def get_notifications(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    unread_only: bool = Query(False, description="Filter to unread notifications only"),
    notification_type: Optional[str] = Query(None, description="Filter by notification type"),
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Get paginated list of notifications for the current user.

    **Filters:**
    - `unread_only`: Only show unread notifications
    - `notification_type`: Filter by specific type (e.g., 'task_created', 'email_received')

    **Pagination:**
    - `page`: Page number (starts at 1)
    - `page_size`: Items per page (max 100)

    **Returns:**
    - List of notifications with pagination metadata
    - Total count and unread count
    """
    logger.info(
        "get_notifications_request",
        user_id=str(current_user.id),
        page=page,
        page_size=page_size,
        unread_only=unread_only,
        notification_type=notification_type,
    )

    result = await notification_service.get_notifications(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        unread_only=unread_only,
        notification_type=notification_type,
    )

    return result


@router.patch("/notifications/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_as_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Mark a specific notification as read.

    **Path Parameters:**
    - `notification_id`: UUID of the notification to mark as read

    **Authorization:**
    - User must own the notification

    **Returns:**
    - Updated notification with `is_read=True` and `read_at` timestamp
    """
    logger.info(
        "mark_notification_read_request",
        user_id=str(current_user.id),
        notification_id=str(notification_id),
    )

    try:
        result = await notification_service.mark_as_read(
            notification_id=notification_id,
            user_id=current_user.id,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )

        return result

    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this notification",
        )


@router.post("/notifications/read-all", response_model=MessageResponse)
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Mark all unread notifications as read for the current user.

    **Returns:**
    - Success message with count of notifications marked as read
    """
    logger.info(
        "mark_all_notifications_read_request",
        user_id=str(current_user.id),
    )

    count = await notification_service.mark_all_as_read(user_id=current_user.id)

    return MessageResponse(
        success=True,
        message=f"Marked {count} notification(s) as read",
        data={"count": count},
    )


@router.delete("/notifications/{notification_id}", response_model=MessageResponse)
async def delete_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Delete a notification.

    **Path Parameters:**
    - `notification_id`: UUID of the notification to delete

    **Authorization:**
    - User must own the notification

    **Returns:**
    - Success message
    """
    logger.info(
        "delete_notification_request",
        user_id=str(current_user.id),
        notification_id=str(notification_id),
    )

    try:
        success = await notification_service.delete_notification(
            notification_id=notification_id,
            user_id=current_user.id,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )

        return MessageResponse(
            success=True,
            message="Notification deleted successfully",
        )

    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this notification",
        )


@router.get("/notifications/unread/count", response_model=dict)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Get count of unread notifications for current user.

    **Returns:**
    - `unread_count`: Number of unread notifications
    """
    logger.debug(
        "get_unread_count_request",
        user_id=str(current_user.id),
    )

    # Get first page with minimal data to retrieve unread count
    result = await notification_service.get_notifications(
        user_id=current_user.id,
        page=1,
        page_size=1,
        unread_only=False,
    )

    return {"unread_count": result.unread_count}
