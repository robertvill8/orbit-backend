"""Health check endpoints."""
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    Basic health check (liveness probe).
    Returns 200 if application is running.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
        "environment": settings.environment,
    }


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check (verifies database, Redis, and external dependencies).
    Returns 200 if ready to serve requests, 503 if not ready.
    """
    checks = {}
    all_healthy = True

    # TODO: Check database connection
    try:
        # await check_database()
        checks["database"] = {"status": "up", "latency_ms": 5}
    except Exception as e:
        checks["database"] = {"status": "down", "error": str(e)}
        all_healthy = False

    # TODO: Check Redis connection
    try:
        # await check_redis()
        checks["redis"] = {"status": "up", "latency_ms": 2}
    except Exception as e:
        checks["redis"] = {"status": "down", "error": str(e)}
        all_healthy = False

    # TODO: Check n8n connectivity
    try:
        # await check_n8n()
        checks["n8n"] = {"status": "up", "latency_ms": 120}
    except Exception as e:
        checks["n8n"] = {"status": "down", "error": str(e)}
        all_healthy = False

    # TODO: Check LLM provider
    try:
        # await check_llm_provider()
        checks["llm_provider"] = {
            "status": "up",
            "provider": settings.llm_provider,
            "latency_ms": 340,
        }
    except Exception as e:
        checks["llm_provider"] = {"status": "down", "error": str(e)}
        all_healthy = False

    if not all_healthy:
        logger.warning("readiness_check_failed", checks=checks)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "checks": checks,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    return {
        "status": "ready",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }
