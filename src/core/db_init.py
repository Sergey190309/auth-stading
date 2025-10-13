from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# from src.core.base import Base
from src.core.settings import settings

# from src.models.user_model import User

# from src.core.utils.utils import create_if_not_exists

admin_db_url = (
    f'{settings.pg_async_prefix}://postgres:postgres@'
    f'{settings.pg_host}:{settings.pg_port}/postgres'
)

admin_engine: AsyncEngine = create_async_engine(
    url=admin_db_url, isolation_level='AUTOCOMMIT', echo=True, future=True
)

db_url = (
    f'{settings.pg_async_prefix}://{settings.pg_user}:{settings.pg_password}@'
    f'{settings.pg_host}:{settings.pg_port}/{settings.pg_db}'
)

engine: AsyncEngine = create_async_engine(
    url=db_url, isolation_level='AUTOCOMMIT', echo=True, future=True
)


# class Base(DeclarativeBase):
#     pass


# async def init_db() -> None:
#     await create_if_not_exists(engine=engine)


async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, expire_on_commit=False
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
    await engine.dispose()  # Close all connections in the pool when done


# --------------------------------------------------------------------------
# Utility to create/drop all tables (for testing or setup scripts)
# --------------------------------------------------------------------------
# async def init_models() -> None:
#     '''Create all tables defined in Base.metadata.'''
#     print(f'\n\nBase: {Base.metadata.tables.keys()}\n\n')
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)


# async def drop_models() -> None:
#     '''Drop all tables.'''
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.drop_all)
