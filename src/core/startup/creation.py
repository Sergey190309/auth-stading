# import asyncio
# from typing import Optional

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.sql import quoted_name

from src.core.settings import settings

ADMIN_DB_URL = (
    f'{settings.pg_async_prefix}://postgres:postgres@'
    f'{settings.pg_host}:{settings.pg_port}/postgres'
)


async def create_user_if_not_exists(
    user_name: str = settings.pg_user,
    password: str = settings.pg_password,
    engine: AsyncEngine = create_async_engine(
        url=ADMIN_DB_URL, isolation_level='AUTOCOMMIT', echo=True, future=True
    ),
) -> list[str]:
    """
    Ensure a PostgreSQL user exist, creating it if necessary.

    Args:
        user_name (str): User_name to create or verify.
        password (str): Password for the user.
        engine (AsyncEngine): Async SQLAlchemy engine for admin operations.

    Returns:
        List[str]: Log messages about actions taken.
    """
    messages: list[str] = []
    # print(f'\n\nuser_name: {user_name}\n')
    try:
        async with engine.begin() as conn:
            """Check and create user"""
            user_exists_query = text(
                'SELECT 1 FROM pg_roles WHERE rolname = :user_name'
            )
            result = await conn.execute(user_exists_query, {'user_name': user_name})
            user_exists = result.scalar_one_or_none()
            if not user_exists:
                await conn.execute(
                    text(f"CREATE USER {user_name} WITH PASSWORD '{password}'")
                )
                messages.append(f"[INFO] User '{user_name}' created.")
                print(messages[-1])
            else:
                messages.append(f"[INFO] User '{user_name}' already exists.")
                print(messages[-1])

    except (SQLAlchemyError, DBAPIError) as e:
        messages.append(f'[ERROR] Database operation failed: {str(e)}')
        print(messages[-1])
        raise
    except Exception as e:
        messages.append(f'[ERROR] Unexpected error: {str(e)}')
        print(messages[-1])
        raise
    finally:
        await engine.dispose()
    return messages


async def create_database_if_not_exists(
    db_name: str,
    engine: AsyncEngine = create_async_engine(
        url=ADMIN_DB_URL, isolation_level='AUTOCOMMIT', echo=True, future=True
    ),
) -> list[str]:
    """Ensure create_database_if_not_exists creates the DB if missing."""
    messages: list[str] = []
    try:
        async with engine.begin() as conn:
            """Check and create database"""
            db_exists_query = text(
                'SELECT 1 FROM pg_database WHERE datname = :db_name'
            )
            result = await conn.execute(db_exists_query, {'db_name': db_name})
            db_exists = result.scalar_one_or_none()
            """Create database outside transaction block"""
            if not db_exists:
                autocommit_engine: AsyncEngine = create_async_engine(
                    url=ADMIN_DB_URL,
                    isolation_level='AUTOCOMMIT',
                    echo=True,
                    future=True,
                )
                async with autocommit_engine.connect() as conn:
                    try:
                        await conn.execute(
                            text(
                                f'CREATE DATABASE {quoted_name(db_name, quote=True)}'
                            )
                        )
                        # f'CREATE DATABASE \'{db_name}\''))
                        messages.append(f"[INFO] Database '{db_name}' created.")
                        print(messages[-1])
                    except SQLAlchemyError as e:
                        # Likely race condition (DB created by another process)
                        messages.append(
                            f"[WARN] Database '{db_name}' may already exist "
                            f'({str(e)}).'
                        )
                        print(messages[-1])
                    finally:
                        await autocommit_engine.dispose()
            else:
                messages.append(f"[INFO] Database '{db_name}' already exists.")
                print(messages[-1])
    except (SQLAlchemyError, DBAPIError) as e:
        messages.append(f'[ERROR] Database operation failed: {str(e)}')
        print(messages[-1])
        raise
    except Exception as e:
        messages.append(f'[ERROR] Unexpected error: {str(e)}')
        print(messages[-1])
        raise
    finally:
        await engine.dispose()
    return messages


async def grant_all_preveleges(
    db_name: str = settings.pg_db,
    user_name: str = settings.pg_user,
    engine: AsyncEngine = create_async_engine(
        url=ADMIN_DB_URL, isolation_level='AUTOCOMMIT', echo=True, future=True
    ),
) -> list[str]:
    """
    Grants all privileges on an existing PostgreSQL database to an existing
        user.

    Args:
        db_name (str): Name of the target database.
        user_name (str): PostgreSQL role/user to grant privileges to.
        engine (AsyncEngine): SQLAlchemy AsyncEngine connected to the admin
            database.

    Returns:
        list[str]: Log messages describing performed actions.
    """
    messages: list[str] = []
    try:
        async with engine.begin() as conn:
            """Verify database and role existence"""
            user_exists_result = await conn.execute(
                text('SELECT 1 FROM pg_roles WHERE rolname = :user_name'), 
                {'user_name': user_name}
            )
            if not user_exists_result.scalar_one_or_none():
                messages.append(f"[ERROR] User '{user_name}' does not exist.")
                print(messages[-1])
                return messages
            db_exists_result = await conn.execute(
                text('SELECT 1 FROM pg_database WHERE datname = :db_name'), 
                {'db_name': db_name}
            )
            if not db_exists_result.scalar_one_or_none():
                messages.append(f"[ERROR] Database '{db_name}' does not exist.")
                print(messages[-1])
                return messages

            """Perform GRANT — double-quoted to safely handle names"""
            """Grant access to database itself"""
            grant_sql = text(
                f'GRANT ALL PRIVILEGES ON DATABASE '
                f'{quoted_name(db_name, quote=True)} TO '
                f'{quoted_name(user_name, quote=True)};'
            )
            await conn.execute(grant_sql)
            """Switch to target DB explicitly (for schema/table grants)"""
            await conn.execute(
                text(
                    f'ALTER DATABASE '
                    f'{quoted_name(db_name, quote=True)} OWNER TO '
                    f'{quoted_name(user_name, quote=True)};'
                )
            )
            """Grant on schema (assuming 'public')"""
            await conn.execute(
                text(
                    'GRANT ALL ON SCHEMA public TO '
                    f'{quoted_name(user_name, quote=True)};'
                )
            )
            """Grant on all existing tables, sequences, and functions"""
            await conn.execute(
                text(
                    'GRANT ALL ON ALL TABLES IN SCHEMA public TO '
                    f'{quoted_name(user_name, quote=True)};'
                )
            )
            await conn.execute(
                text(
                    'GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO '
                    f'{quoted_name(user_name, quote=True)};'
                )
            )
            await conn.execute(
                text(
                    'GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO '
                    f'{quoted_name(user_name, quote=True)};'
                )
            )
            """Grant defaults for future objects"""
            await conn.execute(
                text(
                    f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON '
                    f'TABLES TO {quoted_name(user_name, quote=True)};'
                )
            )
            await conn.execute(
                text(
                    f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON '
                    f'SEQUENCES TO {quoted_name(user_name, quote=True)};'
                )
            )
            await conn.execute(
                text(
                    f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON '
                    f'FUNCTIONS TO {quoted_name(user_name, quote=True)};'
                )
            )

            messages.append(
                '[INFO] Granted all privileges on database '
                f"'{db_name}' to user '{user_name}'."
            )
            print(messages[-1])
        # await engine.dispose()

    except (SQLAlchemyError, DBAPIError) as e:
        msg = f'[ERROR] Database operation failed: {str(e)}'
        messages.append(msg)
        print(msg)
        raise
    except Exception as e:
        msg = f'[ERROR] Unexpected error: {str(e)}'
        messages.append(msg)
        print(msg)
        raise
    finally:
        await engine.dispose()

    return messages
