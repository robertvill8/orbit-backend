"""
Database session management with SQLAlchemy 2.0 async engine.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connection before using
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to provide database sessions to route handlers.

    Yields:
        AsyncSession: SQLAlchemy async session

    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database (create tables if they don't exist).
    This is for development only - use Alembic migrations in production.
    """
    async with engine.begin() as conn:
        # Import all models to register them with Base
        from app.models import user, email, task, document, calendar, relationship, activity, integration

        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close database connection pool.
    Call this during application shutdown.
    """
    await engine.dispose()
