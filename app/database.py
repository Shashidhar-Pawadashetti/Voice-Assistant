"""Database engine, session management, and connectivity health check."""

import asyncio
import logging
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings
from app.models.base import Base


logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Get or initialize the global SQLAlchemy async engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        url = settings.DATABASE_URL

        connect_args = {}
        if url.startswith("sqlite"):
            # Required for SQLite in-memory / file async testing
            connect_args["check_same_thread"] = False
            _engine = create_async_engine(
                url,
                echo=False,
                connect_args=connect_args,
            )
        else:
            _engine = create_async_engine(
                url,
                echo=False,
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
                connect_args=connect_args,
            )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Get or initialize the global session factory."""
    global _sessionmaker
    if _sessionmaker is None:
        engine = get_engine()
        _sessionmaker = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _sessionmaker


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a transactional async database session."""
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_health() -> tuple[bool, str | None, float]:
    """Safe database connectivity check with timeout.

    Returns:
        (is_healthy, error_message, latency_ms)
    """
    settings = get_settings()
    engine = get_engine()
    start_time = asyncio.get_event_loop().time()

    try:
        async with asyncio.timeout(settings.DATABASE_TIMEOUT_SECONDS):
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000.0
        return True, None, round(latency_ms, 2)
    except asyncio.TimeoutError:
        latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000.0
        logger.warning("Database health check timed out")
        return False, "Database ping timed out", round(latency_ms, 2)
    except Exception as exc:
        latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000.0
        # Sanitize exception message so connection credentials are not exposed
        error_type = exc.__class__.__name__
        logger.warning("Database health check failed: %s", error_type)
        return False, f"Connection failed: {error_type}", round(latency_ms, 2)


async def dispose_engine() -> None:
    """Close all connections on application shutdown."""
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _sessionmaker = None
