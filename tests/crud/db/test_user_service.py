# from typing import AsyncGenerator

import pytest

# import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    # AsyncSession,
    # async_sessionmaker,
    # create_async_engine,
)

# from src.core.base import Base
# from src.core.settings import settings
# from src.errors.db_errors import UserAlreadyExistsError
# from src.models.user_model import User
# from src.schemas.user_schema import CreateUserSchema, UserSchema


@pytest.mark.active
@pytest.mark.asyncio
async def test_create_user_success(
    create_empty_test_db: AsyncEngine,
):
    print(f'\n\ncreate_empty_test_db: {create_empty_test_db}\n\n')