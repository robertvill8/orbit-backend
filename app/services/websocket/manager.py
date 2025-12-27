"""
WebSocket connection manager for real-time bidirectional communication.
Manages active WebSocket connections, message routing, and session tracking.
"""
from typing import Dict, List
from uuid import UUID
import json

from fastapi import WebSocket, WebSocketDisconnect
from redis.asyncio import Redis
from structlog import get_logger

logger = get_logger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections for real-time communication.

    Features:
    - Per-session connection tracking
    - Multiple connections per session support
    - Redis-backed session registry
    - Message broadcasting and targeted sending
    - Automatic cleanup on disconnect

    Attributes:
        active_connections: Dict mapping session_id to list of WebSocket connections
        redis: Redis client for distributed session tracking
    """

    def __init__(self, redis_client: Redis):
        """
        Initialize WebSocket manager.

        Args:
            redis_client: Redis client for session registry
        """
        self.active_connections: Dict[UUID, List[WebSocket]] = {}
        self.redis = redis_client

    async def connect(self, session_id: UUID, websocket: WebSocket) -> None:
        """
        Accept and register a new WebSocket connection.

        Args:
            session_id: Session identifier
            websocket: WebSocket connection to register

        Workflow:
            1. Accept WebSocket connection
            2. Add to in-memory connection list
            3. Register in Redis session registry
        """
        await websocket.accept()

        # Add to in-memory connection list
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

        # Register in Redis for distributed tracking
        client_host = websocket.client.host if websocket.client else "unknown"
        await self.redis.sadd(f"ws:session:{session_id}", client_host)

        logger.info(
            "websocket_connected",
            session_id=str(session_id),
            client_host=client_host,
            active_connections=len(self.active_connections[session_id]),
        )

    async def disconnect(self, session_id: UUID, websocket: WebSocket) -> None:
        """
        Unregister and close a WebSocket connection.

        Args:
            session_id: Session identifier
            websocket: WebSocket connection to remove

        Workflow:
            1. Remove from in-memory connection list
            2. Remove from Redis session registry
            3. Clean up session if no more connections
        """
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)

            # Clean up session if no more connections
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

        # Remove from Redis registry
        client_host = websocket.client.host if websocket.client else "unknown"
        await self.redis.srem(f"ws:session:{session_id}", client_host)

        # Clean up Redis key if empty
        count = await self.redis.scard(f"ws:session:{session_id}")
        if count == 0:
            await self.redis.delete(f"ws:session:{session_id}")

        logger.info(
            "websocket_disconnected",
            session_id=str(session_id),
            client_host=client_host,
        )

    async def send_to_session(self, session_id: UUID, message: dict) -> int:
        """
        Send a message to all connections in a session.

        Args:
            session_id: Target session identifier
            message: Message dictionary to send as JSON

        Returns:
            Number of connections message was sent to

        Example:
            count = await manager.send_to_session(
                session_id=uuid.UUID(...),
                message={
                    "type": "notification",
                    "data": {"title": "New task created", "task_id": "..."}
                }
            )
        """
        if session_id not in self.active_connections:
            logger.debug(
                "send_to_session_no_connections",
                session_id=str(session_id),
            )
            return 0

        connections = self.active_connections[session_id]
        sent_count = 0

        for connection in connections:
            try:
                await connection.send_json(message)
                sent_count += 1
            except Exception as e:
                logger.error(
                    "send_to_session_failed",
                    session_id=str(session_id),
                    error=str(e),
                )
                # Connection may be stale, will be cleaned up on next disconnect

        logger.debug(
            "message_sent_to_session",
            session_id=str(session_id),
            message_type=message.get("type"),
            sent_count=sent_count,
        )

        return sent_count

    async def broadcast(self, message: dict, exclude_session: UUID = None) -> int:
        """
        Broadcast a message to all active connections.

        Args:
            message: Message dictionary to send as JSON
            exclude_session: Optional session ID to exclude from broadcast

        Returns:
            Total number of connections message was sent to

        Example:
            count = await manager.broadcast(
                message={"type": "system_announcement", "data": {"text": "Maintenance in 5 min"}},
                exclude_session=current_session_id
            )
        """
        sent_count = 0

        for session_id, connections in self.active_connections.items():
            # Skip excluded session
            if exclude_session and session_id == exclude_session:
                continue

            for connection in connections:
                try:
                    await connection.send_json(message)
                    sent_count += 1
                except Exception as e:
                    logger.error(
                        "broadcast_failed",
                        session_id=str(session_id),
                        error=str(e),
                    )

        logger.info(
            "message_broadcasted",
            message_type=message.get("type"),
            sent_count=sent_count,
            total_sessions=len(self.active_connections),
        )

        return sent_count

    async def send_to_user(self, user_id: UUID, message: dict) -> int:
        """
        Send a message to all sessions belonging to a user.

        Args:
            user_id: Target user identifier
            message: Message dictionary to send as JSON

        Returns:
            Number of connections message was sent to

        Note:
            Requires Redis registry with user-to-session mapping.
            Key format: user:sessions:{user_id} -> Set of session_ids
        """
        # Get all sessions for this user from Redis
        session_ids_bytes = await self.redis.smembers(f"user:sessions:{user_id}")
        session_ids = [UUID(sid) for sid in session_ids_bytes]

        sent_count = 0
        for session_id in session_ids:
            count = await self.send_to_session(session_id, message)
            sent_count += count

        logger.debug(
            "message_sent_to_user",
            user_id=str(user_id),
            sessions_count=len(session_ids),
            sent_count=sent_count,
        )

        return sent_count

    async def get_active_sessions(self) -> List[UUID]:
        """
        Get list of all active session IDs.

        Returns:
            List of active session UUIDs
        """
        return list(self.active_connections.keys())

    async def get_connection_count(self, session_id: UUID = None) -> int:
        """
        Get number of active connections.

        Args:
            session_id: Optional session ID to check specific session

        Returns:
            Number of active connections (total or for specific session)
        """
        if session_id:
            return len(self.active_connections.get(session_id, []))

        return sum(len(conns) for conns in self.active_connections.values())

    async def is_session_connected(self, session_id: UUID) -> bool:
        """
        Check if a session has any active connections.

        Args:
            session_id: Session identifier to check

        Returns:
            True if session has at least one active connection
        """
        return session_id in self.active_connections and len(self.active_connections[session_id]) > 0
