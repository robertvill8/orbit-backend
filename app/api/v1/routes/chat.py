"""Chat and agent endpoints."""
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import get_current_user
from app.db.base import get_db
from app.models.user import User
from app.models.session import Session as DBSession
from app.models.message import Message
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    MessageHistoryResponse,
    MessageItem,
)
from app.services.agent.service import AgentService

router = APIRouter()
logger = get_logger(__name__)


@router.post("/chat/message", response_model=ChatMessageResponse, status_code=status.HTTP_200_OK)
async def send_message(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a text message to the agent and receive a response.

    Workflow:
    1. Create or retrieve session
    2. Process message with agent service
    3. Return response with tool calls

    Args:
        request: Chat message request
        current_user: Authenticated user
        db: Database session

    Returns:
        Chat response with agent reply
    """
    logger.info("send_message_called", user_id=current_user.id, message_length=len(request.message))

    # Get or create session
    session_id = request.session_id
    if not session_id:
        # Create new session
        new_session = DBSession(
            user_id=current_user.id,
            device_info={},
            context_data={},
        )
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        session_id = new_session.session_id
        logger.info("session_created", session_id=session_id)
    else:
        # Verify session belongs to user
        result = await db.execute(
            select(DBSession).where(
                DBSession.session_id == session_id,
                DBSession.user_id == current_user.id,
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or unauthorized",
            )

    # Process message with agent
    agent_service = AgentService(db)
    response = await agent_service.process_message(
        session_id=session_id,
        user_message=request.message,
        user_id=current_user.id,
    )

    logger.info(
        "message_processed",
        session_id=session_id,
        tool_calls_count=len(response.tool_calls) if response.tool_calls else 0,
    )

    return response


@router.post("/chat/voice", status_code=status.HTTP_200_OK)
async def upload_voice(db: AsyncSession = Depends(get_db)):
    """Upload voice recording for transcription and processing."""
    logger.info("upload_voice_called")
    # TODO: Implement voice transcription logic
    return {
        "success": True,
        "data": {
            "message_id": "msg_voice_xyz789",
            "transcription": {
                "text": "Voice transcription endpoint - Implementation pending",
                "confidence": 0.95,
            },
            "response": "Processing voice message...",
        }
    }


@router.get("/chat/history/{session_id}", response_model=MessageHistoryResponse)
async def get_chat_history(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """
    Retrieve conversation history for a session.

    Args:
        session_id: Session ID
        current_user: Authenticated user
        db: Database session
        limit: Maximum number of messages to return
        offset: Pagination offset

    Returns:
        Message history
    """
    logger.info("get_chat_history_called", session_id=session_id, user_id=current_user.id)

    # Verify session belongs to user
    result = await db.execute(
        select(DBSession).where(
            DBSession.session_id == session_id,
            DBSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or unauthorized",
        )

    # Get messages
    messages_query = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    messages_result = await db.execute(messages_query)
    messages = list(messages_result.scalars().all())

    # Get total count
    from sqlalchemy import func
    count_result = await db.execute(
        select(func.count(Message.id)).where(Message.session_id == session_id)
    )
    total_count = count_result.scalar_one()

    # Convert to response format
    message_items = [
        MessageItem(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            metadata=msg.metadata,
            created_at=msg.created_at,
        )
        for msg in messages
    ]

    return MessageHistoryResponse(
        session_id=session_id,
        messages=message_items,
        total_count=total_count,
    )


@router.post("/chat/stream")
async def stream_chat(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Stream LLM response in real-time using Server-Sent Events (SSE).

    This endpoint provides a streaming alternative to /chat/message.
    Responses are streamed token-by-token for a better user experience.

    **Request Body:**
    - Same as /chat/message: `message` and optional `session_id`

    **Response:**
    - Content-Type: text/event-stream
    - Each event is a JSON object with type and data

    **Event Types:**
    - `start`: Streaming started with session_id
    - `token`: Text chunk from LLM response
    - `tool_call`: Tool execution started
    - `tool_result`: Tool execution completed
    - `end`: Streaming completed with message_id and tokens_used
    - `error`: Error occurred during streaming

    **Example Client Usage (JavaScript):**
    ```javascript
    const eventSource = new EventSource('/api/v1/chat/stream', {
        method: 'POST',
        body: JSON.stringify({ message: "Hello" }),
        headers: { 'Authorization': 'Bearer <token>' }
    });

    eventSource.addEventListener('message', (e) => {
        const data = JSON.parse(e.data);
        if (data.type === 'token') {
            appendToChat(data.content);
        } else if (data.type === 'end') {
            eventSource.close();
        }
    });
    ```
    """
    from fastapi.responses import StreamingResponse

    logger.info(
        "stream_chat_called",
        user_id=current_user.id,
        message_length=len(request.message),
    )

    # Get or create session
    session_id = request.session_id
    if not session_id:
        # Create new session
        new_session = DBSession(
            user_id=current_user.id,
            device_info={},
            context_data={},
        )
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        session_id = new_session.session_id
        logger.info("session_created_for_stream", session_id=session_id)
    else:
        # Verify session belongs to user
        result = await db.execute(
            select(DBSession).where(
                DBSession.session_id == session_id,
                DBSession.user_id == current_user.id,
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or unauthorized",
            )

    # Initialize agent service
    agent_service = AgentService(db)

    # Return streaming response
    return StreamingResponse(
        agent_service.stream_response(
            session_id=session_id,
            user_message=request.message,
            user_id=current_user.id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
