"""
Redis connection management and utilities.
"""

from typing import AsyncGenerator, Optional
import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings


class RedisManager:
    """
    Redis connection manager with connection pooling.

    Handles:
    - Connection lifecycle
    - Pub/Sub channels
    - Session registry for WebSocket connections
    """

    def __init__(self):
        self.client: Optional[Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None

    async def connect(self) -> None:
        """Initialize Redis connection pool."""
        self.client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.redis_max_connections,
        )

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.pubsub:
            await self.pubsub.close()
        if self.client:
            await self.client.close()

    def get_client(self) -> Redis:
        """
        Get Redis client instance.

        Returns:
            Redis client

        Raises:
            RuntimeError: If Redis not connected
        """
        if not self.client:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self.client


# Global Redis manager instance
redis_manager = RedisManager()


async def get_redis() -> AsyncGenerator[Redis, None]:
    """
    Dependency function to provide Redis client to route handlers.

    Yields:
        Redis: Redis client instance

    Usage:
        @app.get("/cache")
        async def get_cache(redis: Redis = Depends(get_redis)):
            value = await redis.get("key")
            return {"value": value}
    """
    yield redis_manager.get_client()


async def init_redis() -> None:
    """Initialize Redis connection on application startup."""
    await redis_manager.connect()


async def close_redis() -> None:
    """Close Redis connection on application shutdown."""
    await redis_manager.disconnect()
