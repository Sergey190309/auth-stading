import pytest

from src.core.settings import settings
from tests.consts_and_utils import TEST_DB_NAME, TEST_USER_NAME, TEST_USER_PASSWORD


@pytest.fixture(scope='module')
def test_db_name() -> str:
    return TEST_DB_NAME


@pytest.fixture(scope='module')
def test_user_name() -> str:
    return TEST_USER_NAME


@pytest.fixture(scope='module')
def test_user_password() -> str:
    return TEST_USER_PASSWORD


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
