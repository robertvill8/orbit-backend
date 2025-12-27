"""
Agent service for LLM orchestration with Claude API.
Handles conversation management and tool calling.
"""
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import UUID

import anthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.core.config import settings
from app.models.message import Message, LLMRequest
from app.models.session import Session
from app.models.task import Task
from app.schemas.chat import ChatMessageResponse, ToolCall
from app.services.activity.service import ActivityService
from app.services.integration.service import IntegrationService
from app.services.task.service import TaskService
from app.services.agent.tools import TOOL_DEFINITIONS

logger = get_logger(__name__)


class AgentService:
    """
    Agent orchestration service with Claude API integration.

    Handles:
    - Multi-turn conversations with context management
    - Tool calling (function calling pattern)
    - Session and message persistence
    - Integration with n8n workflows via tools
    - Activity logging
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.anthropic_model
        self.max_tokens = settings.anthropic_max_tokens

        # Initialize dependent services
        self.activity_service = ActivityService(db)
        self.task_service = TaskService(db)
        self.integration_service = IntegrationService(db)

    async def process_message(
        self,
        session_id: UUID,
        user_message: str,
        user_id: UUID,
    ) -> ChatMessageResponse:
        """
        Process a user message and return agent response.

        Workflow:
        1. Store user message
        2. Retrieve conversation history
        3. Call Claude API with tools
        4. Execute any tool calls
        5. Get final response from Claude
        6. Store assistant message
        7. Log activity

        Args:
            session_id: Session ID
            user_message: User's message text
            user_id: User ID

        Returns:
            Chat response with agent reply and tool calls
        """
        start_time = datetime.utcnow()

        # 1. Store user message
        user_msg = await self._store_message(
            session_id=session_id,
            role="user",
            content=user_message,
        )

        # 2. Get conversation history
        conversation_history = await self._get_conversation_history(session_id)

        # 3. Call Claude with tools
        tool_calls_made: List[ToolCall] = []
        total_tokens = 0

        try:
            # Initial Claude call
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                tools=TOOL_DEFINITIONS,
                messages=conversation_history,
            )

            total_tokens += response.usage.input_tokens + response.usage.output_tokens

            # Log LLM request
            await self._log_llm_request(
                session_id=session_id,
                provider="anthropic",
                model_name=self.model,
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens,
                latency_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
            )

            # 4. Handle tool calls (multi-turn if needed)
            while response.stop_reason == "tool_use":
                # Extract tool calls from response
                tool_use_blocks = [
                    block for block in response.content if block.type == "tool_use"
                ]

                # Execute each tool
                tool_results = []
                for tool_use in tool_use_blocks:
                    tool_name = tool_use.name
                    tool_input = tool_use.input

                    logger.info(
                        "tool_call_executing",
                        tool_name=tool_name,
                        tool_input=tool_input,
                    )

                    try:
                        # Execute tool
                        tool_result = await self._execute_tool(
                            tool_name=tool_name,
                            parameters=tool_input,
                            user_id=user_id,
                            session_id=session_id,
                        )

                        tool_calls_made.append(
                            ToolCall(
                                name=tool_name,
                                parameters=tool_input,
                                result=tool_result,
                            )
                        )

                        # Append tool result for next Claude call
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use.id,
                                "content": str(tool_result),
                            }
                        )

                    except Exception as e:
                        logger.error(
                            "tool_execution_failed",
                            tool_name=tool_name,
                            error=str(e),
                        )
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use.id,
                                "content": f"Error: {str(e)}",
                                "is_error": True,
                            }
                        )

                # Continue conversation with tool results
                conversation_history.append(
                    {"role": "assistant", "content": response.content}
                )
                conversation_history.append({"role": "user", "content": tool_results})

                # Get next response from Claude
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    tools=TOOL_DEFINITIONS,
                    messages=conversation_history,
                )

                total_tokens += response.usage.input_tokens + response.usage.output_tokens

            # 5. Extract final text response
            final_text = ""
            for block in response.content:
                if block.type == "text":
                    final_text += block.text

            # 6. Store assistant message
            assistant_msg = await self._store_message(
                session_id=session_id,
                role="assistant",
                content=final_text,
                metadata={
                    "tool_calls": [tc.model_dump() for tc in tool_calls_made],
                    "tokens_used": total_tokens,
                },
            )

            # 7. Log activity
            await self.activity_service.log_activity(
                user_id=user_id,
                session_id=session_id,
                activity_type="message_processed",
                description=f"Agent responded to user message",
                metadata={
                    "user_message": user_message[:100],
                    "tool_calls_count": len(tool_calls_made),
                    "tokens_used": total_tokens,
                },
                related_message_id=assistant_msg.id,
            )

            return ChatMessageResponse(
                id=assistant_msg.id,
                reply=final_text,
                session_id=session_id,
                tool_calls=tool_calls_made if tool_calls_made else None,
                tokens_used=total_tokens,
                created_at=assistant_msg.created_at,
            )

        except Exception as e:
            logger.error(
                "agent_processing_failed",
                error=str(e),
                user_id=user_id,
                session_id=session_id,
            )
            raise

    async def _execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        user_id: UUID,
        session_id: UUID,
    ) -> Dict[str, Any]:
        """
        Execute a tool based on its name.

        Args:
            tool_name: Name of the tool
            parameters: Tool parameters from Claude
            user_id: User ID
            session_id: Session ID

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool name is unknown
        """
        if tool_name == "create_task":
            return await self._tool_create_task(parameters, user_id, session_id)
        elif tool_name == "search_email":
            return await self._tool_search_email(parameters, session_id)
        elif tool_name == "create_calendar_event":
            return await self._tool_create_calendar_event(parameters, session_id)
        elif tool_name == "extract_document_text":
            return await self._tool_extract_document_text(parameters, session_id)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _tool_create_task(
        self,
        parameters: Dict[str, Any],
        user_id: UUID,
        session_id: UUID,
    ) -> Dict[str, Any]:
        """Execute create_task tool."""
        from app.schemas.task import TaskCreate

        # Note: Since tasks require a list_id, we'll need to either:
        # 1. Create a default list for the user
        # 2. Use the first available list
        # For simplicity, we'll return task data and have the frontend handle list assignment

        # Get or create default task list for user
        from app.models.task import TaskList
        from sqlalchemy import select

        result = await self.db.execute(
            select(TaskList).where(TaskList.user_id == user_id).limit(1)
        )
        task_list = result.scalar_one_or_none()

        if not task_list:
            # Create default list
            task_list = TaskList(
                user_id=user_id,
                name="Default",
                position=0,
                color="#3B82F6"
            )
            self.db.add(task_list)
            await self.db.commit()
            await self.db.refresh(task_list)

        # Parse due_date if provided
        due_date = None
        if "due_date" in parameters and parameters["due_date"]:
            from dateutil import parser
            due_date = parser.parse(parameters["due_date"])

        task_data = TaskCreate(
            title=parameters["title"],
            description=parameters.get("description", ""),
            priority=parameters.get("priority", "medium"),
            status="open",
            due_date=due_date,
            list_id=task_list.id,
            metadata={"created_by_agent": True},
        )

        task = await self.task_service.create_task(task_data, user_id, session_id)

        # Log activity
        await self.activity_service.log_activity(
            user_id=user_id,
            session_id=session_id,
            activity_type="task_created",
            description=f"Created task: {task.title}",
            metadata={"task_id": str(task.id)},
            related_task_id=task.id,
        )

        return {
            "success": True,
            "task_id": str(task.id),
            "title": task.title,
            "message": f"Task '{task.title}' created successfully",
        }

    async def _tool_search_email(
        self,
        parameters: Dict[str, Any],
        session_id: UUID,
    ) -> Dict[str, Any]:
        """Execute search_email tool."""
        result = await self.integration_service.search_emails(
            query=parameters["query"],
            from_date=parameters.get("from_date"),
            to_date=parameters.get("to_date"),
            session_id=session_id,
        )
        return result

    async def _tool_create_calendar_event(
        self,
        parameters: Dict[str, Any],
        session_id: UUID,
    ) -> Dict[str, Any]:
        """Execute create_calendar_event tool."""
        result = await self.integration_service.create_calendar_event(
            title=parameters["title"],
            start_time=parameters["start_time"],
            end_time=parameters["end_time"],
            attendees=parameters.get("attendees"),
            session_id=session_id,
        )
        return result

    async def _tool_extract_document_text(
        self,
        parameters: Dict[str, Any],
        session_id: UUID,
    ) -> Dict[str, Any]:
        """Execute extract_document_text tool."""
        text = await self.integration_service.extract_document_text(
            document_path=parameters["document_path"],
            session_id=session_id,
        )
        return {"text": text}

    async def _store_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Message:
        """Store a message in the database."""
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            content_type="text",
            metadata=metadata or {},
        )

        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        return message

    async def _get_conversation_history(
        self,
        session_id: UUID,
        max_messages: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history formatted for Claude API.

        Args:
            session_id: Session ID
            max_messages: Maximum number of messages to retrieve

        Returns:
            List of message dicts in Claude format
        """
        result = await self.db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.desc())
            .limit(max_messages)
        )
        messages = list(result.scalars().all())
        messages.reverse()  # Oldest first

        # Convert to Claude format
        claude_messages = []
        for msg in messages:
            claude_messages.append({"role": msg.role, "content": msg.content})

        return claude_messages

    async def _log_llm_request(
        self,
        session_id: UUID,
        provider: str,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        latency_ms: int,
    ) -> None:
        """Log LLM request to database."""
        llm_request = LLMRequest(
            session_id=session_id,
            provider=provider,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
        )

        self.db.add(llm_request)
        await self.db.commit()

    async def stream_response(
        self,
        session_id: UUID,
        user_message: str,
        user_id: UUID,
    ) -> AsyncGenerator[str, None]:
        """
        Stream agent response using Server-Sent Events (SSE).

        This method yields JSON-formatted strings for SSE streaming.
        Each chunk is a complete JSON object representing a streaming event.

        Args:
            session_id: Session ID
            user_message: User's message text
            user_id: User ID

        Yields:
            JSON strings for SSE events (format: "data: {json}\n\n")

        Example:
            async for chunk in agent_service.stream_response(...):
                yield chunk

        Event Types:
            - "start": Streaming started
            - "token": LLM token chunk
            - "tool_call": Tool execution started
            - "tool_result": Tool execution completed
            - "end": Streaming completed with final message ID
            - "error": Error occurred during streaming
        """
        import json
        from datetime import datetime

        start_time = datetime.utcnow()

        try:
            # Send start event
            yield f"data: {json.dumps({'type': 'start', 'session_id': str(session_id)})}\n\n"

            # Store user message
            user_msg = await self._store_message(
                session_id=session_id,
                role="user",
                content=user_message,
            )

            # Get conversation history
            conversation_history = await self._get_conversation_history(session_id)

            # Call Claude with streaming
            accumulated_text = ""
            tool_calls_made: List[ToolCall] = []
            total_tokens = 0

            # Note: Anthropic's streaming API requires different approach
            # For now, we'll simulate streaming by chunking the response
            # TODO: Implement true streaming with anthropic.AsyncStream

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                tools=TOOL_DEFINITIONS,
                messages=conversation_history,
            )

            total_tokens += response.usage.input_tokens + response.usage.output_tokens

            # Handle tool calls first
            while response.stop_reason == "tool_use":
                tool_use_blocks = [
                    block for block in response.content if block.type == "tool_use"
                ]

                # Execute tools and send events
                tool_results = []
                for tool_use in tool_use_blocks:
                    tool_name = tool_use.name
                    tool_input = tool_use.input

                    # Send tool call start event
                    yield f"data: {json.dumps({'type': 'tool_call', 'tool': tool_name, 'parameters': tool_input})}\n\n"

                    try:
                        tool_result = await self._execute_tool(
                            tool_name=tool_name,
                            parameters=tool_input,
                            user_id=user_id,
                            session_id=session_id,
                        )

                        tool_calls_made.append(
                            ToolCall(
                                name=tool_name,
                                parameters=tool_input,
                                result=tool_result,
                            )
                        )

                        # Send tool result event
                        yield f"data: {json.dumps({'type': 'tool_result', 'tool': tool_name, 'result': tool_result})}\n\n"

                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use.id,
                                "content": str(tool_result),
                            }
                        )

                    except Exception as e:
                        logger.error("tool_execution_failed", tool_name=tool_name, error=str(e))
                        yield f"data: {json.dumps({'type': 'error', 'message': f'Tool {tool_name} failed: {str(e)}'})}\n\n"
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use.id,
                                "content": f"Error: {str(e)}",
                                "is_error": True,
                            }
                        )

                # Continue conversation
                conversation_history.append(
                    {"role": "assistant", "content": response.content}
                )
                conversation_history.append({"role": "user", "content": tool_results})

                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    tools=TOOL_DEFINITIONS,
                    messages=conversation_history,
                )

                total_tokens += response.usage.input_tokens + response.usage.output_tokens

            # Extract final text and stream it in chunks
            final_text = ""
            for block in response.content:
                if block.type == "text":
                    final_text += block.text

            # Stream text in word-by-word chunks for better UX
            words = final_text.split()
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                accumulated_text += chunk
                yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

            # Store assistant message
            assistant_msg = await self._store_message(
                session_id=session_id,
                role="assistant",
                content=accumulated_text,
                metadata={
                    "tool_calls": [tc.model_dump() for tc in tool_calls_made],
                    "tokens_used": total_tokens,
                    "streamed": True,
                },
            )

            # Log LLM request
            await self._log_llm_request(
                session_id=session_id,
                provider="anthropic",
                model_name=self.model,
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                total_tokens=total_tokens,
                latency_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
            )

            # Log activity
            await self.activity_service.log_activity(
                user_id=user_id,
                session_id=session_id,
                activity_type="message_processed",
                description=f"Agent responded to user message (streamed)",
                metadata={
                    "user_message": user_message[:100],
                    "tool_calls_count": len(tool_calls_made),
                    "tokens_used": total_tokens,
                },
                related_message_id=assistant_msg.id,
            )

            # Send end event
            yield f"data: {json.dumps({'type': 'end', 'message_id': str(assistant_msg.id), 'tokens_used': total_tokens})}\n\n"

        except Exception as e:
            logger.error(
                "stream_response_failed",
                error=str(e),
                user_id=user_id,
                session_id=session_id,
            )
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
