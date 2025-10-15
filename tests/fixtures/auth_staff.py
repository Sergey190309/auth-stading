import uuid

import pytest

from src.models.user_model import User


@pytest.fixture
def raw_password() -> str:
    """Provide a consistent plaintext password for tests."""
    return 'SuperSecret123'


@pytest.fixture
def test_user(raw_password: str) -> User:
    """Return a User instance with a hashed password."""
    return User(
        id=uuid.uuid4(),
        email='test@example.com',
        hashed_password=User.hash_password(raw_password),
        full_name='Test User',
        is_active=True,
    )
