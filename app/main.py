"""
FastAPI main application entry point.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.database import close_db
from app.core.redis import redis_manager, init_redis, close_redis
from app.api.v1.routes import health, sessions, chat, tasks, activities, websocket, notifications
from app.api.v1.auth import router as auth_router
from app.services.websocket.manager import WebSocketManager

# Configure logging on import
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifecycle manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(
        "application_starting",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )

    # Initialize Redis connection
    await init_redis()
    logger.info("redis_initialized")

    # Initialize WebSocket manager with Redis client
    redis_client = redis_manager.get_client()
    ws_manager = WebSocketManager(redis_client=redis_client)
    app.state.ws_manager = ws_manager
    logger.info("websocket_manager_initialized")

    # Start background tasks if enabled (TODO)

    yield

    # Shutdown
    logger.info("application_shutting_down")

    # Close database connections
    await close_db()

    # Close Redis connections
    await close_redis()
    logger.info("redis_closed")

    # Stop background tasks (TODO)


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI Agent Cockpit Backend - Intelligent orchestration layer for proactive personal assistant",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus metrics instrumentation
if settings.prometheus_enabled:
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Include API routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth_router, prefix="/api/v1", tags=["Authentication"])
app.include_router(sessions.router, prefix="/api/v1", tags=["Sessions"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(tasks.router, prefix="/api/v1", tags=["Tasks"])
app.include_router(activities.router, prefix="/api/v1", tags=["Activities"])
app.include_router(websocket.router, prefix="/api/v1", tags=["WebSocket"])
app.include_router(notifications.router, prefix="/api/v1", tags=["Notifications"])


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled exceptions."""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": str(exc) if settings.debug else "The server encountered an error while processing your request.",
            },
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
        workers=1 if settings.reload else settings.workers,
    )
