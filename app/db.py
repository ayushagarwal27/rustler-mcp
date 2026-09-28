from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(
    settings.resolved_database_url,
    connect_args=settings.asyncpg_connect_args,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    echo=False,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Short-lived session per tool call. This server never writes, so no
    explicit commit/rollback handling is needed beyond the context manager."""
    async with SessionLocal() as session:
        yield session
