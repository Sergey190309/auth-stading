from typing import AsyncIterator, Callable

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
)

from src.core.settings import settings


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
