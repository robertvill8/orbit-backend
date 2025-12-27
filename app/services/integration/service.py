"""
Integration service for orchestrating n8n workflow calls.
Provides high-level interface for tool execution.
"""
import time
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.services.integration.n8n_client import N8nClient

logger = get_logger(__name__)


class IntegrationService:
    """
    High-level service for managing integrations.
    Orchestrates n8n workflows and logs all calls.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.n8n_client = N8nClient()

    async def call_workflow(
        self,
        workflow_name: str,
        payload: Dict[str, Any],
        session_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Generic workflow caller with logging.

        Args:
            workflow_name: Name of the workflow ('email_search', 'calendar_create', etc.)
            payload: Workflow input data
            session_id: Session ID for logging

        Returns:
            Workflow execution result

        Raises:
            Exception: If workflow call fails
        """
        start_time = time.time()
        error_message = None
        response_status = 500
        response_payload = None

        try:
            if workflow_name == "email_search":
                response_payload = await self.n8n_client.search_emails(
                    query=payload.get("query", ""),
                    from_date=payload.get("from_date"),
                    to_date=payload.get("to_date"),
                )
            elif workflow_name == "calendar_create":
                response_payload = await self.n8n_client.create_calendar_event(
                    title=payload.get("title", ""),
                    start_time=payload.get("start_time", ""),
                    end_time=payload.get("end_time", ""),
                    attendees=payload.get("attendees"),
                )
            elif workflow_name == "document_ocr":
                response_payload = await self.n8n_client.extract_document_text(
                    document_path=payload.get("document_path", "")
                )
            else:
                raise ValueError(f"Unknown workflow name: {workflow_name}")

            response_status = 200
            return response_payload

        except Exception as e:
            error_message = str(e)
            logger.error(
                "workflow_call_failed",
                workflow_name=workflow_name,
                error=error_message,
            )
            raise

        finally:
            latency_ms = int((time.time() - start_time) * 1000)

            # Log integration call to database
            await self.n8n_client.log_integration_call(
                db=self.db,
                session_id=session_id,
                integration_name=f"n8n_{workflow_name}",
                workflow_id=workflow_name,
                request_method="POST",
                request_url=f"{self.n8n_client.base_url}/webhook/{workflow_name}",
                request_payload=payload,
                response_status=response_status,
                response_payload=response_payload,
                error_message=error_message,
                latency_ms=latency_ms,
            )

    async def search_emails(
        self,
        query: str,
        session_id: Optional[UUID] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search emails via n8n workflow.

        Args:
            query: Search query
            session_id: Session ID
            from_date: Start date filter
            to_date: End date filter

        Returns:
            Email search results
        """
        payload = {
            "query": query,
            "from_date": from_date,
            "to_date": to_date,
        }

        return await self.call_workflow("email_search", payload, session_id)

    async def create_calendar_event(
        self,
        title: str,
        start_time: str,
        end_time: str,
        session_id: Optional[UUID] = None,
        attendees: Optional[list[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create calendar event via n8n workflow.

        Args:
            title: Event title
            start_time: Start time (ISO format)
            end_time: End time (ISO format)
            session_id: Session ID
            attendees: List of attendee emails

        Returns:
            Created event data
        """
        payload = {
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "attendees": attendees or [],
        }

        return await self.call_workflow("calendar_create", payload, session_id)

    async def extract_document_text(
        self,
        document_path: str,
        session_id: Optional[UUID] = None,
    ) -> str:
        """
        Extract text from document via n8n OCR workflow.

        Args:
            document_path: Path to document file
            session_id: Session ID

        Returns:
            Extracted text content
        """
        payload = {
            "document_path": document_path,
        }

        result = await self.call_workflow("document_ocr", payload, session_id)
        return result.get("text", "")
