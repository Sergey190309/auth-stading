from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.sql import quoted_name

from src.core.base import Base

TEST_DB_NAME = 'test_db_name'
TEST_USER_NAME = 'test_user_name'
TEST_USER_EMAIL = 'test@example.com'
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


async def create_test_db(engine: AsyncEngine, db_name: str = TEST_DB_NAME) -> None:
    async with engine.connect() as conn:
        # Check existence (param-binding is fine for SELECT)
        db_exists_result = await conn.execute(
            text('SELECT 1 FROM pg_database WHERE datname = :db_name'),
            {'db_name': db_name},
        )
        if db_exists_result.scalar():
            return
        await conn.execute(text(f'CREATE DATABASE {db_name}'))


async def grant_preveleges(
    engine: AsyncEngine, db_name: str = TEST_DB_NAME, user_name: str = TEST_USER_NAME
) -> None:
    async with engine.begin() as conn:
        db_exists_result = await conn.execute(
            text('SELECT 1 FROM pg_database WHERE datname = :db_name'),
            {'db_name': db_name},
        )
        if not db_exists_result.scalar():
            print(f'\n\nDatabase {db_name} does not exist\n\n')
            return
        user_exists_result = await conn.execute(
            text('SELECT 1 FROM pg_roles WHERE rolname = :user_name'),
            {'user_name': user_name},
        )
        if not user_exists_result.scalar():
            print(f'\n\nUser {user_name} does not exist\n\n')
            return

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


async def remove_db(engine: AsyncEngine, db_name: str = TEST_DB_NAME) -> None:
    """
    Terminates all active connections to the specified PostgreSQL database
    and drops it safely.
    """
    terminate_sql = text("""
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = :db_name
        AND pid <> pg_backend_pid();
    """)
    async with engine.connect() as conn:
        await conn.execute(terminate_sql, {"db_name": db_name})
        await conn.execute(text(f'DROP DATABASE IF EXISTS {db_name}'))


async def remove_user(
    engine: AsyncEngine,
    user_name: str = TEST_USER_NAME,
    db_name: str = TEST_DB_NAME,
    schema_name: str = 'public',
) -> None:
    async with engine.begin() as conn:
        safe_user_name = quoted_name(user_name, quote=True)
        safe_db_name = quoted_name(db_name, quote=True)
        safe_schema_name = quoted_name(schema_name, quote=True)

        statements = [
            ('REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA '
             f'{safe_schema_name} FROM {safe_user_name}'),
            ('REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA '
             f'{safe_schema_name} FROM {safe_user_name}'),
            ('REVOKE ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA '
             f'{safe_schema_name} FROM {safe_user_name}'),
            (f'REVOKE ALL PRIVILEGES ON DATABASE {safe_db_name} FROM '
             f'{safe_user_name}'),
            # optional cleanup
            f'REASSIGN OWNED BY {safe_user_name} TO CURRENT_USER',
            f'DROP OWNED BY {safe_user_name}',
        ]
        for stmt in statements:
            try:
                await conn.execute(text(stmt))
            except Exception as e:
                print(f"[WARN] Failed executing: {stmt}\nError: {e}")

        await conn.execute(text(f'DROP USER IF EXISTS {safe_user_name}'))

async def create_tables(engine: AsyncEngine) -> None:
    """Create all tables defined in Base.metadata."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
