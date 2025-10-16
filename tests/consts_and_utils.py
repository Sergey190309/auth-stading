from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.sql import quoted_name

TEST_DB_NAME = 'test_db_name'
TEST_USER_NAME = 'test_user_name'
TEST_USER_PASSWORD = 'test_user_password'


async def create_test_user(
    engine: AsyncEngine,
    user_name: str = TEST_USER_NAME,
    password: str = TEST_USER_PASSWORD,
) -> None:
    """check whether user exists"""
    # Use a plain connection and enable autocommit so DDL (CREATE USER)
    # runs outside a transaction block.
    async with engine.connect() as conn:
        # Check existence (param-binding is fine for SELECT)
        user_exists_result = await conn.execute(
            text('SELECT 1 FROM pg_roles WHERE rolname = :user_name'),
            {'user_name': user_name},
        )
        if user_exists_result.scalar():
            return
        # Quote the identifier to safely place it into SQL text
        safe_name = quoted_name(user_name, quote=True)

        # Escape single quotes in password and inline as a quoted literal
        escaped_password = password.replace("'", "''")
        create_user_sql = (
            f"CREATE USER {safe_name} WITH PASSWORD '{escaped_password}'"
        )
        await conn.execute(text(create_user_sql))
