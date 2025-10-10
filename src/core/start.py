from src.core.db_init import engine, init_models
from src.core.settings import settings
from src.core.startup.creation import (
    create_database_if_not_exists,
    create_user_if_not_exists,
    grant_all_preveleges,
)


async def startup() -> None:
    print('\n\nStartup\n\n')
    await create_user_if_not_exists(
        engine=engine,
        user_name=settings.pg_user,
        password=settings.pg_password,
    )
    await create_database_if_not_exists(
        engine=engine,
        db_name=settings.pg_db,
    )
    await grant_all_preveleges(
        engine=engine,
        db_name=settings.pg_db,
        user_name=settings.pg_user,
    )
    await init_models()