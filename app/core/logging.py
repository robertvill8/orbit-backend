"""
Structured logging configuration using structlog.
All logs are formatted as JSON for machine parsing and observability.
"""
import logging
import sys
from typing import Any, Dict

import structlog
from structlog.types import Processor

from app.core.config import settings


def configure_logging() -> None:
    """Configure structured logging with structlog."""

    # Determine log level from settings
    log_level = getattr(logging, settings.log_level, logging.INFO)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Define processors for structlog
    processors: list[Processor] = [
        # Add logger name to event dict
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        # Stack info for exceptions
        structlog.processors.StackInfoRenderer(),
        # Format exceptions
        structlog.processors.format_exc_info,
    ]

    # Add development-friendly console renderer if not in production
    if settings.is_development:
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        # Use JSON renderer for production
        processors.append(structlog.processors.JSONRenderer())

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("user_logged_in", user_id="123", session_id="abc")
    """
    return structlog.get_logger(name)


def add_context(**kwargs: Any) -> None:
    """
    Add context to all subsequent log messages in this thread.

    Args:
        **kwargs: Key-value pairs to add to log context

    Example:
        >>> add_context(request_id="req_123", user_id="user_456")
        >>> logger.info("processing_request")  # Will include request_id and user_id
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context(*keys: str) -> None:
    """
    Clear specific context variables or all if no keys provided.

    Args:
        *keys: Context keys to clear. If empty, clears all context.

    Example:
        >>> clear_context("request_id")
        >>> clear_context()  # Clear all context
    """
    if keys:
        structlog.contextvars.unbind_contextvars(*keys)
    else:
        structlog.contextvars.clear_contextvars()


class LoggerMixin:
    """
    Mixin to add structured logging to any class.

    Usage:
        class MyService(LoggerMixin):
            def process(self):
                self.logger.info("processing_started", item_count=10)
    """

    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Get logger instance for this class."""
        if not hasattr(self, "_logger"):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger
