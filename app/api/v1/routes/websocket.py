"""WebSocket endpoints for real-time bidirectional communication."""
import asyncio
from datetime import datetime, UTC
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.database import get_db
from app.core.security import verify_token
from app.services.agent.service import AgentService
from app.schemas.chat import ChatMessageResponse

router = APIRouter()
logger = get_logger(__name__)


async def verify_websocket_token(token: str = Query(..., description="JWT access token")) -> UUID:
    """
    Verify JWT token for WebSocket authentication.

    Args:
        token: JWT access token from query parameter

    Returns:
        User ID from token

    Raises:
        HTTPException: If token is invalid or expired
    """
    user_id_str = verify_token(token, token_type="access")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    try:
        return UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
        )


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(..., description="JWT access token"),
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint for real-time bidirectional communication.

    Features:
    - JWT authentication via query parameter
    - Message handling with AgentService integration
    - Heartbeat ping/pong support
    - Automatic session management

    Args:
        websocket: WebSocket connection
        session_id: Session identifier
        token: JWT access token for authentication
        db: Database session

    Message Types:
        Client -> Server:
            - "message": User text message to agent
            - "ping": Heartbeat ping

        Server -> Client:
            - "connection_established": Initial connection confirmation
            - "message": Agent response to user message
            - "notification": Proactive notification from system
            - "pong": Heartbeat response
            - "error": Error message

    Example WebSocket URL:
        ws://localhost:8000/api/v1/ws/{session_id}?token={jwt_token}
    """
    # Verify authentication
    try:
        user_id = await verify_websocket_token(token)
    except HTTPException as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=e.detail)
        return

    # Parse session ID
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA, reason="Invalid session ID format")
        return

    # Get WebSocket manager from app state (will be set in main.py)
    ws_manager = websocket.app.state.ws_manager

    # Connect to WebSocket manager
    await ws_manager.connect(session_uuid, websocket)

    logger.info(
        "websocket_connected",
        session_id=session_id,
        user_id=str(user_id),
    )

    try:
        # Send connection established message
        await websocket.send_json({
            "type": "connection_established",
            "data": {
                "session_id": session_id,
                "user_id": str(user_id),
                "connected_at": datetime.now(UTC).isoformat(),
            }
        })

        # Initialize AgentService for message processing
        agent_service = AgentService(db)

        # Keep connection open and handle incoming messages
        while True:
            data = await websocket.receive_json()

            message_type = data.get("type")
            logger.debug(
                "websocket_message_received",
                session_id=session_id,
                user_id=str(user_id),
                message_type=message_type,
            )

            # Handle ping/pong heartbeat
            if message_type == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now(UTC).isoformat(),
                })
                continue

            # Handle user message
            if message_type == "message":
                try:
                    user_message = data.get("message", "").strip()
                    if not user_message:
                        await websocket.send_json({
                            "type": "error",
                            "error": {
                                "code": "EMPTY_MESSAGE",
                                "message": "Message cannot be empty",
                            }
                        })
                        continue

                    # Process message with agent service
                    response: ChatMessageResponse = await agent_service.process_message(
                        session_id=session_uuid,
                        user_message=user_message,
                        user_id=user_id,
                    )

                    # Send agent response
                    await websocket.send_json({
                        "type": "message",
                        "data": {
                            "id": str(response.id),
                            "reply": response.reply,
                            "session_id": str(response.session_id),
                            "tool_calls": [tc.model_dump() for tc in response.tool_calls] if response.tool_calls else None,
                            "tokens_used": response.tokens_used,
                            "created_at": response.created_at.isoformat(),
                        }
                    })

                    logger.info(
                        "websocket_message_processed",
                        session_id=session_id,
                        user_id=str(user_id),
                        message_id=str(response.id),
                        tokens_used=response.tokens_used,
                    )

                except Exception as e:
                    logger.error(
                        "websocket_message_processing_failed",
                        session_id=session_id,
                        user_id=str(user_id),
                        error=str(e),
                        exc_info=True,
                    )
                    await websocket.send_json({
                        "type": "error",
                        "error": {
                            "code": "PROCESSING_ERROR",
                            "message": "Failed to process message",
                            "details": str(e),
                        }
                    })

            else:
                # Unknown message type
                logger.warning(
                    "websocket_unknown_message_type",
                    session_id=session_id,
                    user_id=str(user_id),
                    message_type=message_type,
                )
                await websocket.send_json({
                    "type": "error",
                    "error": {
                        "code": "UNKNOWN_MESSAGE_TYPE",
                        "message": f"Unknown message type: {message_type}",
                    }
                })

    except WebSocketDisconnect:
        logger.info(
            "websocket_disconnected",
            session_id=session_id,
            user_id=str(user_id),
        )
    except Exception as e:
        logger.error(
            "websocket_error",
            session_id=session_id,
            user_id=str(user_id),
            error=str(e),
            exc_info=True,
        )
    finally:
        # Cleanup connection
        await ws_manager.disconnect(session_uuid, websocket)
