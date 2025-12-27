"""
Unit tests for Notification service.
Tests notification creation, retrieval, updates, and deletion.
"""
import pytest
from uuid import uuid4
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.notification.service import NotificationService
from app.schemas.notification import NotificationCreate
from app.models.notification import Notification


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    db.scalar = AsyncMock()
    return db


@pytest.fixture
def mock_ws_manager():
    """Mock WebSocket manager."""
    ws_manager = AsyncMock()
    ws_manager.send_to_user = AsyncMock(return_value=1)
    return ws_manager


@pytest.fixture
def notification_service(mock_db, mock_ws_manager):
    """Notification service instance with mocked dependencies."""
    return NotificationService(db=mock_db, ws_manager=mock_ws_manager)


@pytest.fixture
def sample_notification_create():
    """Sample notification creation data."""
    return NotificationCreate(
        user_id=uuid4(),
        title="New Task Created",
        content="Task 'Review document' has been created",
        type="task_created",
        action={"type": "open_task", "url": "/tasks/123"},
        related_entity_type="task",
        related_entity_id=uuid4(),
    )


class TestNotificationService:
    """Test suite for NotificationService."""

    @pytest.mark.asyncio
    async def test_create_notification_success(
        self, notification_service, mock_db, mock_ws_manager, sample_notification_create
    ):
        """Test creating a notification successfully."""
        # Mock database operations
        created_notification = Notification(
            id=uuid4(),
            user_id=sample_notification_create.user_id,
            title=sample_notification_create.title,
            content=sample_notification_create.content,
            type=sample_notification_create.type,
            action=sample_notification_create.action,
            related_entity_type=sample_notification_create.related_entity_type,
            related_entity_id=sample_notification_create.related_entity_id,
            is_read=False,
            read_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        async def mock_refresh(obj):
            """Mock refresh by copying created_notification attributes."""
            for key, value in vars(created_notification).items():
                if not key.startswith("_"):
                    setattr(obj, key, value)

        mock_db.refresh = mock_refresh

        # Create notification
        result = await notification_service.create_notification(sample_notification_create)

        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

        # Verify WebSocket notification sent
        mock_ws_manager.send_to_user.assert_called_once()

        # Verify response
        assert result.title == sample_notification_create.title
        assert result.content == sample_notification_create.content
        assert result.type == sample_notification_create.type
        assert not result.is_read

    @pytest.mark.asyncio
    async def test_create_notification_without_websocket(
        self, mock_db, sample_notification_create
    ):
        """Test creating notification without WebSocket manager."""
        # Create service without WebSocket manager
        service = NotificationService(db=mock_db, ws_manager=None)

        created_notification = Notification(
            id=uuid4(),
            user_id=sample_notification_create.user_id,
            title=sample_notification_create.title,
            content=sample_notification_create.content,
            type=sample_notification_create.type,
            is_read=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        async def mock_refresh(obj):
            for key, value in vars(created_notification).items():
                if not key.startswith("_"):
                    setattr(obj, key, value)

        mock_db.refresh = mock_refresh

        # Create notification
        result = await service.create_notification(sample_notification_create)

        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

        # Verify no WebSocket send attempted
        assert result is not None

    @pytest.mark.asyncio
    async def test_create_notification_websocket_failure_does_not_block(
        self, notification_service, mock_db, mock_ws_manager, sample_notification_create
    ):
        """Test that WebSocket failure doesn't prevent notification creation."""
        # Make WebSocket send fail
        mock_ws_manager.send_to_user = AsyncMock(
            side_effect=Exception("WebSocket error")
        )

        created_notification = Notification(
            id=uuid4(),
            user_id=sample_notification_create.user_id,
            title=sample_notification_create.title,
            content=sample_notification_create.content,
            type=sample_notification_create.type,
            is_read=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        async def mock_refresh(obj):
            for key, value in vars(created_notification).items():
                if not key.startswith("_"):
                    setattr(obj, key, value)

        mock_db.refresh = mock_refresh

        # Create notification should succeed despite WebSocket failure
        result = await notification_service.create_notification(sample_notification_create)

        # Verify notification was created
        assert result is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_notifications_with_pagination(
        self, notification_service, mock_db
    ):
        """Test retrieving paginated notifications."""
        user_id = uuid4()

        # Mock database queries
        mock_db.scalar = AsyncMock(side_effect=[25, 5])  # total_count, unread_count

        # Mock notification results
        mock_notifications = [
            Notification(
                id=uuid4(),
                user_id=user_id,
                title=f"Notification {i}",
                content=f"Content {i}",
                type="test_type",
                is_read=i % 2 == 0,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            for i in range(20)
        ]

        mock_result = AsyncMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=lambda: mock_notifications))
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Get notifications
        result = await notification_service.get_notifications(
            user_id=user_id,
            page=1,
            page_size=20,
        )

        # Verify response
        assert result.total_count == 25
        assert result.unread_count == 5
        assert result.page == 1
        assert result.page_size == 20
        assert result.has_next is True
        assert len(result.notifications) == 20

    @pytest.mark.asyncio
    async def test_get_notifications_filter_unread_only(
        self, notification_service, mock_db
    ):
        """Test retrieving only unread notifications."""
        user_id = uuid4()

        # Mock database queries
        mock_db.scalar = AsyncMock(side_effect=[5, 5])  # total_count, unread_count

        mock_notifications = [
            Notification(
                id=uuid4(),
                user_id=user_id,
                title=f"Unread {i}",
                content=f"Content {i}",
                type="test_type",
                is_read=False,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            for i in range(5)
        ]

        mock_result = AsyncMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=lambda: mock_notifications))
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Get unread notifications
        result = await notification_service.get_notifications(
            user_id=user_id,
            page=1,
            page_size=20,
            unread_only=True,
        )

        # Verify all returned notifications are unread
        assert all(not n.is_read for n in result.notifications)

    @pytest.mark.asyncio
    async def test_mark_as_read_success(self, notification_service, mock_db):
        """Test marking a notification as read."""
        user_id = uuid4()
        notification_id = uuid4()

        # Mock notification
        notification = Notification(
            id=notification_id,
            user_id=user_id,
            title="Test Notification",
            content="Test content",
            type="test",
            is_read=False,
            read_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=notification)
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Mark as read
        result = await notification_service.mark_as_read(notification_id, user_id)

        # Verify notification was marked as read
        assert result is not None
        assert notification.is_read is True
        assert notification.read_at is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_as_read_not_found(self, notification_service, mock_db):
        """Test marking non-existent notification as read."""
        user_id = uuid4()
        notification_id = uuid4()

        # Mock not found
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Mark as read should return None
        result = await notification_service.mark_as_read(notification_id, user_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_mark_as_read_unauthorized(self, notification_service, mock_db):
        """Test marking another user's notification as read."""
        user_id = uuid4()
        other_user_id = uuid4()
        notification_id = uuid4()

        # Mock notification belonging to different user
        notification = Notification(
            id=notification_id,
            user_id=other_user_id,
            title="Test Notification",
            content="Test content",
            type="test",
            is_read=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=notification)
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Mark as read should raise PermissionError
        with pytest.raises(PermissionError):
            await notification_service.mark_as_read(notification_id, user_id)

    @pytest.mark.asyncio
    async def test_mark_all_as_read(self, notification_service, mock_db):
        """Test marking all notifications as read."""
        user_id = uuid4()

        # Mock update result
        mock_result = AsyncMock()
        mock_result.rowcount = 5
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Mark all as read
        count = await notification_service.mark_all_as_read(user_id)

        # Verify count
        assert count == 5
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_notification_success(self, notification_service, mock_db):
        """Test deleting a notification."""
        user_id = uuid4()
        notification_id = uuid4()

        # Mock notification
        notification = Notification(
            id=notification_id,
            user_id=user_id,
            title="Test Notification",
            content="Test content",
            type="test",
            is_read=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        mock_select_result = AsyncMock()
        mock_select_result.scalar_one_or_none = MagicMock(return_value=notification)

        # Mock execute to return different results for select and delete
        call_count = 0

        async def mock_execute_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_select_result
            return AsyncMock()

        mock_db.execute = AsyncMock(side_effect=mock_execute_side_effect)

        # Delete notification
        result = await notification_service.delete_notification(notification_id, user_id)

        # Verify deleted
        assert result is True
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_notification_not_found(self, notification_service, mock_db):
        """Test deleting non-existent notification."""
        user_id = uuid4()
        notification_id = uuid4()

        # Mock not found
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Delete should return False
        result = await notification_service.delete_notification(notification_id, user_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_notification_unauthorized(self, notification_service, mock_db):
        """Test deleting another user's notification."""
        user_id = uuid4()
        other_user_id = uuid4()
        notification_id = uuid4()

        # Mock notification belonging to different user
        notification = Notification(
            id=notification_id,
            user_id=other_user_id,
            title="Test Notification",
            content="Test content",
            type="test",
            is_read=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=notification)
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Delete should raise PermissionError
        with pytest.raises(PermissionError):
            await notification_service.delete_notification(notification_id, user_id)
