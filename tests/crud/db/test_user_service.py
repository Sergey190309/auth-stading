# from typing import AsyncGenerator

from datetime import datetime
from uuid import UUID

import pytest

# import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    # AsyncSession,
    async_sessionmaker,
    # create_async_engine,
)

from src.crud.db.user_service import create_user, get_user_by_email
from src.errors.db_errors import UserAlreadyExistsError, UserNotFoundError
from src.schemas.user_schema import CreateUserSchema

# from src.core.base import Base
# from src.core.settings import settings
# from src.errors.db_errors import UserAlreadyExistsError
# from src.models.user_model import User
# from src.schemas.user_schema import CreateUserSchema, UserSchema


# @pytest.mark.active
@pytest.mark.asyncio
async def test_create_user(
    test_user_email: str,
    test_user_password: str,
    create_empty_test_db: AsyncEngine,
) -> None:
    create_user_schema = CreateUserSchema(
        email=test_user_email,
        password=test_user_password,
    )
    async_session = async_sessionmaker(
        bind=create_empty_test_db, expire_on_commit=False
    )
    async with async_session() as session:
        result1 = await create_user(session=session, user=create_user_schema)
        assert isinstance(result1.id, UUID)
        assert result1.email == test_user_email
        assert result1.is_active
        assert isinstance(result1.created_at, datetime)
        # result2 = await create_user(session=session, user=create_user_schema)
        with pytest.raises(UserAlreadyExistsError) as exec_info:
            await create_user(session=session, user=create_user_schema)
            assert 'User already exists' in str(exec_info.value)


@pytest.mark.active
@pytest.mark.asyncio
async def test_get_user_by_email(
    test_user_email: str,
    test_user_password: str,
    create_empty_test_db: AsyncEngine,
) -> None:
    create_user_schema = CreateUserSchema(
        email=test_user_email,
        password=test_user_password,
    )
    async_session = async_sessionmaker(
        bind=create_empty_test_db, expire_on_commit=False
    )
    '''find existing user by email'''
    async with async_session() as session:
        await create_user(session=session, user=create_user_schema)
        result1 = await get_user_by_email(session=session, email=test_user_email)
        if result1:
            assert result1.email == test_user_email
            assert result1.is_active
            assert isinstance(result1.created_at, datetime)
        '''fine nonexisting user'''
        with pytest.raises(UserNotFoundError) as exec_info:
            await get_user_by_email(
                session=session, email='nonexisting@example.com')
            assert 'User not found exists' in str(exec_info.value)

    
