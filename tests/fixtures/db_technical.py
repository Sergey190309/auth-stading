from typing import AsyncGenerator, Callable

import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
)

from tests.consts_and_utils import create_test_user


@pytest_asyncio.fixture(scope='function')
async def async_engine_factory_func() -> Callable[
    [str], AsyncGenerator[AsyncEngine, None]
]:
    """
    Returns a factory that yields a temporary AsyncEngine for a given URL.
    Automatically disposes it afterward.
    """

    async def _factory(async_url: str) -> AsyncGenerator[AsyncEngine, None]:
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


@pytest_asyncio.fixture(scope='function')
async def async_admin_engine_instance(
    async_admin_url: str,
) -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(
        async_admin_url,
        isolation_level='AUTOCOMMIT',
        echo=True,
        future=True,
    )
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture(scope='function')
async def async_user_test_db_engine_instance(
    async_user_url_test_db: str,
) -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(
        async_user_url_test_db,
        isolation_level='AUTOCOMMIT',
        echo=True,
        future=True,
    )
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture(scope='function')
async def create_empty_test_db(
    async_admin_engine_instance: AsyncEngine,
    async_user_test_db_engine_instance: AsyncEngine,
    test_user_name: str,
) -> AsyncGenerator[AsyncEngine]:
    # pytest will inject the yielded AsyncEngine instance from the
    # `async_admin_engine_instance` fixture, so treat it as an AsyncEngine here.
    engine: AsyncEngine = async_admin_engine_instance
    # create the test user on the admin engine
    await create_test_user(engine=engine, user_name=test_user_name)
    try:
        # yield the engine connected to the test DB for consumers
        yield async_user_test_db_engine_instance
    finally:
        # do not dispose the admin engine here — the provider fixture
        # `async_admin_engine_instance` is responsible for teardown.
        pass
