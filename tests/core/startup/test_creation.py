from typing import AsyncIterator, Callable

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    create_async_engine,
)

from src.core.settings import settings
from src.core.startup.creation import (
    create_database_if_not_exists,
    create_user_if_not_exists,
    grant_all_preveleges,
)


@pytest.fixture(scope='module')
def test_db_name() -> str:
    return 'test_db_name'


@pytest.fixture(scope='module')
def test_user_name() -> str:
    return 'test_user'


@pytest.fixture(scope='module')
def test_user_password() -> str:
    return 'test_password'


@pytest.fixture(scope='module')
def async_admin_url() -> str:
    """Fixture to provide the admin database URL."""
    url: str = (
        f'{settings.pg_async_prefix}://postgres:postgres@'
        f'{settings.pg_host}:{settings.pg_port}/postgres'
    )
    return url


@pytest.fixture(scope='module')
def async_admin_url_test_db(
    test_user_name: str, test_user_password: str, test_db_name: str
) -> str:
    """Fixture to provide the admin database URL."""
    url: str = (
        f'{settings.pg_async_prefix}://postgres:postgres@'
        f'{settings.pg_host}:{settings.pg_port}/{test_db_name}'
    )
    return url


@pytest.fixture(scope='module')
def async_user_url_test_db(
    test_user_name: str, test_user_password: str, test_db_name: str
) -> str:
    """Fixture to provide the admin database URL."""
    url: str = (
        f'{settings.pg_async_prefix}://{test_user_name}:{test_user_password}@'
        f'{settings.pg_host}:{settings.pg_port}/{test_db_name}'
    )
    return url


@pytest_asyncio.fixture(scope='function')
async def async_engine_factory() -> Callable[[str], AsyncIterator[AsyncEngine]]:
    async def _factory(async_url: str) -> AsyncIterator[AsyncEngine]:
        engine: AsyncEngine = create_async_engine(
            url=async_url,
            isolation_level='AUTOCOMMIT',
            echo=True,
            future=True,
        )
        try:
            yield engine
        finally:
            await engine.dispose()

    return _factory


# @pytest.mark.active
@pytest.mark.asyncio
async def test_create_user_if_not_exists(
    test_user_name: str,
    test_user_password: str,
    async_engine_factory: Callable[[str], AsyncIterator[AsyncEngine]],
    async_admin_url: str,
) -> None:
    """Clean up if exists"""
    async for engine in async_engine_factory(async_admin_url):
        async with engine.begin() as conn:
            # Check if the user exists
            user_exists_result = await conn.execute(
                text('SELECT 1 FROM pg_roles WHERE rolname = :username'),
                {'username': test_user_name},
            )
            if user_exists_result.scalar() is not None:
                # Revoke all privileges from the role
                # await conn.execute(text(f'REVOKE ALL PRIVILEGES ON DATABASE
                # {test_db_name} FROM {test_user_name}'))
                # Reassign owned objects to postgres (or another admin role)
                # await conn.execute(text(f'REASSIGN OWNED BY {test_user_name}
                # TO postgres'))
                # Drop the role
                await conn.execute(text(f'DROP ROLE IF EXISTS {test_user_name}'))

            """Create user that does not exist"""
            result0 = await create_user_if_not_exists(
                user_name=test_user_name,
                password=test_user_password,
                engine=engine,
            )
            assert f"[INFO] User '{test_user_name}' created." in result0
            """Create user that already exists"""
            result1 = await create_user_if_not_exists(
                user_name=test_user_name,
                password=test_user_password,
                engine=engine,
            )
            assert (f"[INFO] User '{test_user_name}' already exists.") in result1

            """Check if user exists from db"""
            result3 = await conn.execute(
                text('SELECT 1 FROM pg_roles WHERE rolname = :user_name'),
                {'user_name': test_user_name},
            )
            exists = result3.scalar_one_or_none()
            assert exists == 1


# @pytest.mark.active
@pytest.mark.asyncio
async def test_create_database_if_not_exists(
    test_db_name: str,
    async_engine_factory: Callable[[str], AsyncIterator[AsyncEngine]],
    async_admin_url: str,
) -> None:
    """Ensure create_database_if_not_exists creates the DB if missing."""

    """Clean up if db exists"""
    async for engine in async_engine_factory(async_admin_url):
        async with engine.begin() as conn:
            await conn.execute(text(f'DROP DATABASE IF EXISTS {test_db_name}'))

        """Create database that does not exist"""
        messages: list[str] = await create_database_if_not_exists(
            db_name=test_db_name,
            engine=engine,
        )
        assert f"[INFO] Database '{test_db_name}' created." in messages

        """Create database that already exists"""
        messages: list[str] = await create_database_if_not_exists(
            db_name=test_db_name,
            engine=engine,
        )
        assert f"[INFO] Database '{test_db_name}' already exists." in messages

        """Check if database exists from db"""
        async with engine.begin() as conn:
            result = await conn.execute(
                text('SELECT 1 FROM pg_database WHERE datname = :dbname'),
                {'dbname': test_db_name},
            )
            exists = result.scalar_one_or_none()
            # print(f'\n\nexists: {exists}\n')
            assert exists == 1

        """Cleanup"""
        # async with engine.connect() as conn:
        #     await conn.execute(text(f'DROP DATABASE IF EXISTS {test_db_name}'))


@pytest.mark.active
@pytest.mark.asyncio
async def test_grant_all_preveleges(
    test_db_name: str,
    test_user_name: str,
    test_user_password: str,
    async_engine_factory: Callable[[str], AsyncIterator[AsyncEngine]],
    async_admin_url: str,
    async_admin_url_test_db: str,
) -> None:
    """
    Test granting privileges on an existing DB to an existing user.
    """
    messages: list[str] = []
    async def terminate_db_connections(conn: AsyncConnection, db_name: str) -> None:
        """Terminate all connections to a database."""
        await conn.execute(
            text("""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = :db_name
                AND pid <> pg_backend_pid();
            """),
            {"db_name": db_name}
        )
    """PREPARE: create test DB and user"""
    async for engine in async_engine_factory(async_admin_url):
        async with engine.connect() as conn:
            """Drop user and db if they exist (avoid conflicts)"""
            await conn.execute(text(f'DROP DATABASE IF EXISTS {test_db_name}'))
            await conn.execute(text(f'DROP ROLE IF EXISTS {test_user_name}'))

            """Test acts without db and user"""
            messages = await grant_all_preveleges(
                db_name=test_db_name,
                user_name=test_user_name,
                engine=engine,
            )
            assert (f"[ERROR] User '{test_user_name}' does not exist.") in messages

            """Create user"""
            await conn.execute(
                text(
                    f'CREATE USER {test_user_name} WITH PASSWORD '
                    f"'{test_user_password}'"
                )
            )

            """Test acts without db"""
            messages = await grant_all_preveleges(
                db_name=test_db_name,
                user_name=test_user_name,
                engine=engine,
            )
            assert (f"[ERROR] Database '{test_db_name}' does not exist.") in messages
            """Create test DB"""
            await conn.execute(text(f'CREATE DATABASE {test_db_name}'))
        await engine.dispose()

    """Test acts with db and user"""
    async for engine in async_engine_factory(async_admin_url_test_db):
        async with engine.connect() as conn:
            messages = await grant_all_preveleges(
                db_name=test_db_name,
                user_name=test_user_name,
                engine=engine,
            )
            assert (
                '[INFO] Granted all privileges on database '
                f"'{test_db_name}' to user '{test_user_name}'."
            ) in messages
            print(f'\n\nmessages: {messages}\n\n')
        await engine.dispose()

    #         result = await conn.execute(
    #             text("""
    #             SELECT datname as database_name,
    #                 has_database_privilege(:username, datname, 'CONNECT') 
    #                     as can_connect,
    #                 has_database_privilege(:username, datname, 'CREATE') 
    #                     as can_create,
    #                 has_database_privilege(:username, datname, 'TEMPORARY') 
    #                     as can_temp
    #             FROM pg_database
    #             WHERE datname NOT IN ('template0', 'template1')
    #             ORDER BY datname
    #         """),
    #             {'username': test_user_name},
    #         )
    #         return_data = [dict(row) for row in result.mappings()]
    #         # return_data = result.fetchall()
    #         for item in return_data:
    #             if item['database_name'] == test_db_name:
    #                 assert item['can_connect']
    #                 assert item['can_create']
    #                 assert item['can_temp']

    # async for engine in async_engine_factory(async_admin_url):
    #     async with engine.begin() as conn:
    #         result = await conn.execute(
    #             text("""
    #                 SELECT grantee, table_schema, table_name, privilege_type
    #                 FROM information_schema.role_table_grants
    #                 WHERE grantee = :username
    #                 ORDER BY table_schema, table_name, privilege_type;
    #             """),
    #             {'username': test_user_name},
    #         )
    #         return_data = [dict(row) for row in result.mappings()]
    #         print(f'\n\nreturn_data: {return_data}\n\n')
    """
    --- CLEANUP ---
    Revoke privileges and remove DB/user
    """
    async for engine in async_engine_factory(async_admin_url):
        async with engine.begin() as conn:
            await terminate_db_connections(conn, test_db_name)
            await conn.execute(
                text(
                    'REVOKE ALL PRIVILEGES ON DATABASE '
                    f'{test_db_name} FROM {test_user_name}'
                )
            )
            await conn.execute(text(f'DROP DATABASE IF EXISTS {test_db_name}'))
            await conn.execute(text(f'DROP ROLE IF EXISTS {test_user_name}'))

            # print(f'\n\nmessages: {messages}\n\n')
