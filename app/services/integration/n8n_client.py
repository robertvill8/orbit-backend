"""
N8N HTTP client with retry logic and error handling.
Provides typed interfaces for calling n8n webhooks.
"""
import asyncio
from typing import Any, Dict, Optional
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.core.config import settings
from app.models.integration import IntegrationLog

logger = get_logger(__name__)


class N8nClient:
    """
    HTTP client for n8n webhook calls with retry logic.

    Handles:
    - Exponential backoff retry (3 attempts)
    - Request/response logging
    - Circuit breaker pattern (future enhancement)
    - Timeout management
    """

    def __init__(self):
        self.base_url = settings.n8n_base_url
        self.timeout = settings.n8n_timeout_seconds
        self.max_retries = settings.n8n_max_retries
        self.api_key = settings.n8n_api_key

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to n8n webhook with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: Webhook endpoint path
            payload: Request payload

        Returns:
            Response JSON data

        Raises:
            httpx.HTTPError: If request fails after retries
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPError)),
            reraise=True,
        )
        async def _execute_with_retry():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(
                    "n8n_request_start",
                    method=method,
                    url=url,
                    payload=payload,
                )

                if method.upper() == "POST":
                    response = await client.post(url, json=payload, headers=headers)
                elif method.upper() == "GET":
                    response = await client.get(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()

                logger.info(
                    "n8n_request_success",
                    method=method,
                    url=url,
                    status_code=response.status_code,
                )

                return response.json()

        try:
            return await _execute_with_retry()
        except httpx.HTTPError as e:
            logger.error(
                "n8n_request_failed",
                method=method,
                url=url,
                error=str(e),
            )
            raise

    async def search_emails(
        self, query: str, from_date: Optional[str] = None, to_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call n8n email search workflow.

        Args:
            query: Search query string
            from_date: Start date (ISO format)
            to_date: End date (ISO format)

        Returns:
            Email search results
        """
        payload = {
            "query": query,
            "from_date": from_date,
            "to_date": to_date,
        }

        return await self._make_request(
            method="POST",
            endpoint=settings.n8n_webhook_email_read,
            payload=payload,
        )

    async def create_calendar_event(
        self,
        title: str,
        start_time: str,
        end_time: str,
        attendees: Optional[list[str]] = None,
    ) -> Dict[str, Any]:
        """
        Call n8n calendar event creation workflow.

        Args:
            title: Event title
            start_time: Start time (ISO format)
            end_time: End time (ISO format)
            attendees: List of attendee email addresses

        Returns:
            Created event data
        """
        payload = {
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "attendees": attendees or [],
        }

        return await self._make_request(
            method="POST",
            endpoint=settings.n8n_webhook_calendar_create,
            payload=payload,
        )

    async def extract_document_text(self, document_path: str) -> Dict[str, Any]:
        """
        Call n8n OCR workflow to extract text from document.

        Args:
            document_path: Path to document file

        Returns:
            Extracted text and metadata
        """
        payload = {
            "document_path": document_path,
        }

        return await self._make_request(
            method="POST",
            endpoint=settings.n8n_webhook_ocr_process,
            payload=payload,
        )

    async def log_integration_call(
        self,
        db: AsyncSession,
        session_id: Optional[UUID],
        integration_name: str,
        workflow_id: Optional[str],
        request_method: str,
        request_url: str,
        request_payload: Optional[Dict[str, Any]],
        response_status: int,
        response_payload: Optional[Dict[str, Any]],
        error_message: Optional[str],
        latency_ms: int,
    ) -> None:
        """
        Log integration call to database for audit trail.

        Args:
            db: Database session
            session_id: Session ID
            integration_name: Name of integration (e.g., 'n8n_email')
            workflow_id: n8n workflow ID
            request_method: HTTP method
            request_url: Full request URL
            request_payload: Request payload
            response_status: HTTP status code
            response_payload: Response payload
            error_message: Error message if failed
            latency_ms: Request latency in milliseconds
        """
        log_entry = IntegrationLog(
            session_id=session_id,
            integration_name=integration_name,
            workflow_id=workflow_id,
            request_method=request_method,
            request_url=request_url,
            request_payload=request_payload,
            response_status=response_status,
            response_payload=response_payload,
            error_message=error_message,
            latency_ms=latency_ms,
        )

        db.add(log_entry)
        await db.commit()

        logger.info(
            "integration_log_created",
            integration_name=integration_name,
            status=response_status,
            latency_ms=latency_ms,
        )
