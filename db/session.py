"""Async SQLAlchemy engine and session factory for Postgres."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession


def build_engine(database_url: str) -> AsyncEngine:
    """Create the async engine used for all database access.

    Args:
        database_url (str): An `postgresql+asyncpg://` connection string.

    Returns:
        AsyncEngine: A configured async engine, not yet connected.
    """
    return create_async_engine(database_url, pool_pre_ping=True)


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create a session factory bound to the given engine.

    Uses SQLModel's `AsyncSession`, which adds `.exec()` (returning model instances
    directly) on top of SQLAlchemy's session.

    Args:
        engine (AsyncEngine): The engine sessions will use.

    Returns:
        async_sessionmaker[AsyncSession]: A factory producing `AsyncSession` instances.
    """
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def session_scope(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession]:
    """Open a session for one unit of work, committing on success and rolling back on error.

    Args:
        factory (async_sessionmaker[AsyncSession]): The session factory to use.

    Yields:
        AsyncSession: An open session, active for the lifetime of the `with` block.

    Raises:
        Exception: Re-raises whatever the wrapped block raised, after rolling back.
    """
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
