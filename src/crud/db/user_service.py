from sqlalchemy import select
from sqlalchemy.exc import DBAPIError, IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.errors.db_errors import UserAlreadyExistsError, UserNotFoundError
from src.models.user_model import User
from src.schemas.user_schema import CreateUserSchema, UserSchema


async def create_user(
    session: AsyncSession, user: CreateUserSchema
) -> UserSchema:
    try:
        existing_user: User | None = await session.scalar(
            select(User).where(User.email == user.email)
        )
        if existing_user:
            raise UserAlreadyExistsError('User already exists')
        new_user = User(**user.model_dump())
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return UserSchema.model_validate(new_user)
    except UserAlreadyExistsError:
        await session.rollback()
        raise
    except IntegrityError:
        await session.rollback()
        raise UserAlreadyExistsError('User already exists')
    except (SQLAlchemyError, DBAPIError) as e:
        raise RuntimeError(f'Database error: {str(e)}') from e
    except Exception as e:
        raise RuntimeError(f'Unexpected error: {str(e)}') from e


async def get_user_by_email(
    session: AsyncSession, email: str
) -> UserSchema | None:
    try:
        query = select(User).where(User.email == email)
        result = await session.execute(query)
        user_in_db: User | None = result.scalars().one_or_none()
        # replay: UserSchema = UserSchema.model_validate(user_in_db)
        if user_in_db:
            return UserSchema.model_validate(user_in_db)
        raise UserNotFoundError('User not found exists')
    except UserNotFoundError:
        raise
    except (SQLAlchemyError, DBAPIError) as e:
        raise RuntimeError(f'Database error: {str(e)}') from e
    except Exception as e:
        raise RuntimeError(f'Unexpected error: {str(e)}') from e
