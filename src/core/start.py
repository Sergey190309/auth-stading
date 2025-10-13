from sqlalchemy.ext.asyncio import AsyncEngine

from src.core.base import Base
from src.core.db_init import admin_engine, engine
from src.core.settings import settings
from src.core.startup.creation import (
    create_database_if_not_exists,
    create_user_if_not_exists,
    grant_all_preveleges,
)
from src.models.user_model import User  # type: ignore # noqa: F401


async def create_all_tables(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def startup() -> None:
    print('\n\nStartup\n\n')
    await create_user_if_not_exists(
        engine=admin_engine,
        user_name=settings.pg_user,
        password=settings.pg_password,
    )
    await create_database_if_not_exists(
        engine=admin_engine,
        db_name=settings.pg_db,
    )
    await grant_all_preveleges(
        engine=admin_engine,
        db_name=settings.pg_db,
        user_name=settings.pg_user,
    )
    await create_all_tables(engine=engine)
    # print('\n\nStartup complete\n\n')