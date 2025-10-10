from typing import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
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
    '''Fixture to provide the admin database URL.'''
    url: str = (
        f'{settings.pg_async_prefix}://postgres:postgres@'
        f'{settings.pg_host}:{settings.pg_port}/postgres'
    )
    return url


@pytest_asyncio.fixture(scope='function')
async def admin_engine(
    async_admin_url: str,
) -> AsyncIterator[AsyncEngine]:
    engine: AsyncEngine = create_async_engine(
        url=async_admin_url,
        isolation_level='AUTOCOMMIT',
        echo=True,
        future=True,
    )
    try:
        yield engine
    finally:
        await engine.dispose()


# @pytest.mark.active
@pytest.mark.asyncio
async def test_create_user_if_not_exists(
    test_user_name: str,
    test_user_password: str,
    admin_engine: AsyncEngine,
) -> None:
    '''Clean up if exists'''
    async with admin_engine.begin() as conn:
        await conn.execute(text(f'DROP ROLE IF EXISTS {test_user_name}'))
    '''Create user that does not exist'''
    result0 = await create_user_if_not_exists(
        user_name=test_user_name,
        password=test_user_password,
        engine=admin_engine,
    )
    assert f'[INFO] User \'{test_user_name}\' created.' in result0
    '''Create user that already exists'''
    result1 = await create_user_if_not_exists(
        user_name=test_user_name,
        password=test_user_password,
        engine=admin_engine,
    )
    assert f'[INFO] User \'{test_user_name}\' already exists.' in result1

    '''Check if user exists from db'''
    async with admin_engine.begin() as conn:
        result3 = await conn.execute(
            text('SELECT 1 FROM pg_roles WHERE rolname = :user_name'),
            {'user_name': test_user_name},
        )
        exists = result3.scalar_one_or_none()
        # print(f'\n\nexists: {exists}\n')
        assert exists == 1

    # print(f'\n\nresult1: {result1}\n\n')


# @pytest.mark.active
@pytest.mark.asyncio
async def test_create_database_if_not_exists(
    test_db_name: str,
    admin_engine: AsyncEngine,
) -> None:
    '''Ensure create_database_if_not_exists creates the DB if missing.'''

    '''Clean up if it exists'''
    async with admin_engine.connect() as conn:
        await conn.execute(text(f'DROP DATABASE IF EXISTS {test_db_name}'))

    '''Create database that does not exist'''
    messages: list[str] = await create_database_if_not_exists(
        db_name=test_db_name,
        engine=admin_engine,
    )
    assert f'[INFO] Database \'{test_db_name}\' created.' in messages

    '''Create database that already exists'''
    messages: list[str] = await create_database_if_not_exists(
        db_name=test_db_name,
        engine=admin_engine,
    )
    assert f'[INFO] Database \'{test_db_name}\' already exists.' in messages

    '''Check if database exists from db'''
    async with admin_engine.begin() as conn:
        result = await conn.execute(
            text('SELECT 1 FROM pg_database WHERE datname = :dbname'),
            {'dbname': test_db_name},
        )
        exists = result.scalar_one_or_none()
        # print(f'\n\nexists: {exists}\n')
        assert exists == 1

    # 🧹 Cleanup
    # async with admin_engine.connect() as conn:
    #     await conn.execute(text(f'DROP DATABASE IF EXISTS {test_db_name}'))


# @pytest.mark.active
@pytest.mark.asyncio
async def test_grant_all_preveleges(
    test_db_name: str,
    test_user_name: str,
    test_user_password: str,
    admin_engine: AsyncEngine) -> None:
    '''
    Test granting privileges on an existing DB to an existing user.
    '''
    '''PREPARE: create test DB and user'''
    async with admin_engine.connect() as conn:
        '''Drop user and db if they exist (avoid conflicts)'''
        await conn.execute(text(f'DROP DATABASE IF EXISTS {test_db_name}'))
        await conn.execute(text(f'DROP ROLE IF EXISTS {test_user_name}'))

        '''Test acts without db and user'''
        messages: list[str] = await grant_all_preveleges(
            db_name=test_db_name,
            user_name=test_user_name,
            engine=admin_engine,
        )
        assert f'[ERROR] User \'{test_user_name}\' does not exist.' in messages
        
        '''Create user'''
        await conn.execute(text(
            f'CREATE USER {test_user_name} WITH PASSWORD '
            f'\'{test_user_password}\''))

        '''Test acts without db'''
        messages: list[str] = await grant_all_preveleges(
            db_name=test_db_name,
            user_name=test_user_name,
            engine=admin_engine,
        )
        assert (f'[ERROR] Database \'{test_db_name}\' does not exist'
            '.') in messages
        '''Create test DB'''

        await conn.execute(text(
            f'CREATE DATABASE {test_db_name}'))

        '''Test acts with db and user'''
        messages: list[str] = await grant_all_preveleges(
            db_name=test_db_name,
            user_name=test_user_name,
            engine=admin_engine,
        )
        assert ('[INFO] Granted all privileges on database '
                f'\'{test_db_name}\' to user \'{test_user_name}\'.') in messages
        
        '''
        --- CLEANUP ---
        Revoke privileges and remove DB/user
        '''
        await conn.execute(text('REVOKE ALL PRIVILEGES ON DATABASE '
                                f'{test_db_name} FROM {test_user_name}'))
        await conn.execute(text(f'DROP DATABASE IF EXISTS {test_db_name}'))
        await conn.execute(text(f'DROP ROLE IF EXISTS {test_user_name}'))

        print(f'\n\nmessages: {messages}\n\n')

