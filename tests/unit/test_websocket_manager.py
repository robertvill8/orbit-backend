"""
Unit tests for WebSocket manager.
Tests connection management, message routing, and session tracking.
"""
import pytest
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.websocket.manager import WebSocketManager


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = AsyncMock()
    redis.sadd = AsyncMock()
    redis.srem = AsyncMock()
    redis.scard = AsyncMock(return_value=0)
    redis.delete = AsyncMock()
    redis.smembers = AsyncMock(return_value=set())
    return redis


@pytest.fixture
def ws_manager(mock_redis):
    """WebSocket manager instance with mocked Redis."""
    return WebSocketManager(redis_client=mock_redis)


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection."""
    websocket = AsyncMock()
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock()
    websocket.client = MagicMock()
    websocket.client.host = "127.0.0.1"
    return websocket


class TestWebSocketManager:
    """Test suite for WebSocketManager."""

    @pytest.mark.asyncio
    async def test_connect_new_session(self, ws_manager, mock_websocket, mock_redis):
        """Test connecting first WebSocket to a session."""
        session_id = uuid4()

        await ws_manager.connect(session_id, mock_websocket)

        # Verify WebSocket accepted
        mock_websocket.accept.assert_called_once()

        # Verify added to active connections
        assert session_id in ws_manager.active_connections
        assert mock_websocket in ws_manager.active_connections[session_id]

        # Verify Redis registration
        mock_redis.sadd.assert_called_once_with(
            f"ws:session:{session_id}",
            "127.0.0.1"
        )

    @pytest.mark.asyncio
    async def test_connect_multiple_to_same_session(
        self, ws_manager, mock_websocket, mock_redis
    ):
        """Test connecting multiple WebSockets to the same session."""
        session_id = uuid4()
        websocket2 = AsyncMock()
        websocket2.accept = AsyncMock()
        websocket2.client = MagicMock()
        websocket2.client.host = "127.0.0.2"

        # Connect first WebSocket
        await ws_manager.connect(session_id, mock_websocket)

        # Connect second WebSocket to same session
        await ws_manager.connect(session_id, websocket2)

        # Verify both in active connections
        assert len(ws_manager.active_connections[session_id]) == 2
        assert mock_websocket in ws_manager.active_connections[session_id]
        assert websocket2 in ws_manager.active_connections[session_id]

    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(
        self, ws_manager, mock_websocket, mock_redis
    ):
        """Test disconnecting a WebSocket removes it from tracking."""
        session_id = uuid4()

        # Connect first
        await ws_manager.connect(session_id, mock_websocket)

        # Then disconnect
        await ws_manager.disconnect(session_id, mock_websocket)

        # Verify removed from active connections
        assert session_id not in ws_manager.active_connections

        # Verify Redis cleanup
        mock_redis.srem.assert_called_once_with(
            f"ws:session:{session_id}",
            "127.0.0.1"
        )
        mock_redis.delete.assert_called_once_with(f"ws:session:{session_id}")

    @pytest.mark.asyncio
    async def test_disconnect_with_remaining_connections(
        self, ws_manager, mock_websocket, mock_redis
    ):
        """Test disconnecting one WebSocket when others remain."""
        session_id = uuid4()
        websocket2 = AsyncMock()
        websocket2.accept = AsyncMock()
        websocket2.client = MagicMock()
        websocket2.client.host = "127.0.0.2"

        # Connect two WebSockets
        await ws_manager.connect(session_id, mock_websocket)
        await ws_manager.connect(session_id, websocket2)

        # Disconnect first one
        mock_redis.scard = AsyncMock(return_value=1)  # One connection remains
        await ws_manager.disconnect(session_id, mock_websocket)

        # Verify session still exists with one connection
        assert session_id in ws_manager.active_connections
        assert len(ws_manager.active_connections[session_id]) == 1
        assert websocket2 in ws_manager.active_connections[session_id]

        # Verify Redis key not deleted
        mock_redis.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_to_session_success(
        self, ws_manager, mock_websocket, mock_redis
    ):
        """Test sending message to a session."""
        session_id = uuid4()
        message = {"type": "notification", "data": {"text": "Hello"}}

        # Connect WebSocket
        await ws_manager.connect(session_id, mock_websocket)

        # Send message
        count = await ws_manager.send_to_session(session_id, message)

        # Verify message sent
        assert count == 1
        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_to_session_no_connections(self, ws_manager, mock_redis):
        """Test sending message to session with no active connections."""
        session_id = uuid4()
        message = {"type": "notification", "data": {"text": "Hello"}}

        # Send message without connecting any WebSockets
        count = await ws_manager.send_to_session(session_id, message)

        # Verify no messages sent
        assert count == 0

    @pytest.mark.asyncio
    async def test_send_to_session_handles_errors(
        self, ws_manager, mock_websocket, mock_redis
    ):
        """Test sending message handles WebSocket errors gracefully."""
        session_id = uuid4()
        message = {"type": "notification", "data": {"text": "Hello"}}

        # Connect WebSocket
        await ws_manager.connect(session_id, mock_websocket)

        # Make send_json raise an exception
        mock_websocket.send_json = AsyncMock(side_effect=Exception("Connection lost"))

        # Send message should not raise, but return 0
        count = await ws_manager.send_to_session(session_id, message)
        assert count == 0

    @pytest.mark.asyncio
    async def test_broadcast_to_all_sessions(self, ws_manager, mock_redis):
        """Test broadcasting message to all active sessions."""
        session_id1 = uuid4()
        session_id2 = uuid4()
        websocket1 = AsyncMock()
        websocket1.accept = AsyncMock()
        websocket1.send_json = AsyncMock()
        websocket1.client = MagicMock()
        websocket1.client.host = "127.0.0.1"

        websocket2 = AsyncMock()
        websocket2.accept = AsyncMock()
        websocket2.send_json = AsyncMock()
        websocket2.client = MagicMock()
        websocket2.client.host = "127.0.0.2"

        # Connect two sessions
        await ws_manager.connect(session_id1, websocket1)
        await ws_manager.connect(session_id2, websocket2)

        # Broadcast message
        message = {"type": "system", "data": {"text": "Maintenance"}}
        count = await ws_manager.broadcast(message)

        # Verify both received message
        assert count == 2
        websocket1.send_json.assert_called_once_with(message)
        websocket2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_exclude_session(self, ws_manager, mock_redis):
        """Test broadcasting with excluded session."""
        session_id1 = uuid4()
        session_id2 = uuid4()
        websocket1 = AsyncMock()
        websocket1.accept = AsyncMock()
        websocket1.send_json = AsyncMock()
        websocket1.client = MagicMock()
        websocket1.client.host = "127.0.0.1"

        websocket2 = AsyncMock()
        websocket2.accept = AsyncMock()
        websocket2.send_json = AsyncMock()
        websocket2.client = MagicMock()
        websocket2.client.host = "127.0.0.2"

        # Connect two sessions
        await ws_manager.connect(session_id1, websocket1)
        await ws_manager.connect(session_id2, websocket2)

        # Broadcast excluding session_id1
        message = {"type": "system", "data": {"text": "Maintenance"}}
        count = await ws_manager.broadcast(message, exclude_session=session_id1)

        # Verify only session_id2 received message
        assert count == 1
        websocket1.send_json.assert_not_called()
        websocket2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_to_user(self, ws_manager, mock_redis):
        """Test sending message to all sessions of a user."""
        user_id = uuid4()
        session_id1 = uuid4()
        session_id2 = uuid4()

        # Mock Redis to return user's sessions
        mock_redis.smembers = AsyncMock(
            return_value={str(session_id1), str(session_id2)}
        )

        websocket1 = AsyncMock()
        websocket1.accept = AsyncMock()
        websocket1.send_json = AsyncMock()
        websocket1.client = MagicMock()
        websocket1.client.host = "127.0.0.1"

        websocket2 = AsyncMock()
        websocket2.accept = AsyncMock()
        websocket2.send_json = AsyncMock()
        websocket2.client = MagicMock()
        websocket2.client.host = "127.0.0.2"

        # Connect sessions
        await ws_manager.connect(session_id1, websocket1)
        await ws_manager.connect(session_id2, websocket2)

        # Send to user
        message = {"type": "notification", "data": {"text": "New task"}}
        count = await ws_manager.send_to_user(user_id, message)

        # Verify both sessions received message
        assert count == 2
        websocket1.send_json.assert_called_once_with(message)
        websocket2.send_json.assert_called_once_with(message)

        # Verify Redis lookup
        mock_redis.smembers.assert_called_once_with(f"user:sessions:{user_id}")

    @pytest.mark.asyncio
    async def test_get_active_sessions(self, ws_manager, mock_websocket, mock_redis):
        """Test retrieving list of active session IDs."""
        session_id1 = uuid4()
        session_id2 = uuid4()

        # Initially empty
        sessions = await ws_manager.get_active_sessions()
        assert len(sessions) == 0

        # Connect two sessions
        await ws_manager.connect(session_id1, mock_websocket)

        websocket2 = AsyncMock()
        websocket2.accept = AsyncMock()
        websocket2.client = MagicMock()
        websocket2.client.host = "127.0.0.2"
        await ws_manager.connect(session_id2, websocket2)

        # Verify both in active sessions
        sessions = await ws_manager.get_active_sessions()
        assert len(sessions) == 2
        assert session_id1 in sessions
        assert session_id2 in sessions

    @pytest.mark.asyncio
    async def test_get_connection_count(self, ws_manager, mock_websocket, mock_redis):
        """Test getting connection count."""
        session_id = uuid4()

        # Initially zero
        count = await ws_manager.get_connection_count()
        assert count == 0

        # Connect one WebSocket
        await ws_manager.connect(session_id, mock_websocket)

        # Total count should be 1
        total_count = await ws_manager.get_connection_count()
        assert total_count == 1

        # Session-specific count should be 1
        session_count = await ws_manager.get_connection_count(session_id)
        assert session_count == 1

    @pytest.mark.asyncio
    async def test_is_session_connected(self, ws_manager, mock_websocket, mock_redis):
        """Test checking if session is connected."""
        session_id = uuid4()

        # Initially not connected
        is_connected = await ws_manager.is_session_connected(session_id)
        assert not is_connected

        # Connect WebSocket
        await ws_manager.connect(session_id, mock_websocket)

        # Now connected
        is_connected = await ws_manager.is_session_connected(session_id)
        assert is_connected

        # Disconnect
        await ws_manager.disconnect(session_id, mock_websocket)

        # Not connected again
        is_connected = await ws_manager.is_session_connected(session_id)
        assert not is_connected
