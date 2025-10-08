from __future__ import annotations

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.core.settings import settings

db_url = (
    f"postgresql+asyncpg://{settings.pg_user}:{settings.pg_passwod}@"
    f"{settings.pg_host}:{settings.pg_port}/{settings.pg_db}"
)

engine: AsyncEngine = create_async_engine(url=db_url, echo=True, future=True)


class Base(DeclarativeBase):
    pass


async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
    await engine.dispose()  # Close all connections in the pool when done


# --------------------------------------------------------------------------
# Utility to create/drop all tables (for testing or setup scripts)
# --------------------------------------------------------------------------
async def init_models() -> None:
    """Create all tables defined in Base.metadata."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_models() -> None:
    """Drop all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
