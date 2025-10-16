from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, TypedDict

import bcrypt
from jose import jwt
from sqlalchemy import Boolean, String, func
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.base import Base
from src.core.settings import settings


class TokenPayload(TypedDict):
    user_id: str
    exp: datetime


class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f'User(id={self.id}, email={self.email})'
    
    def to_dict(self) -> dict[str, str]:
        return {
            'id': str(self.id),
            'email': self.email,
            'full_name': self.full_name,
            'is_active': str(self.is_active),
            'created_at': str(self.created_at),
        }

    @staticmethod
    def hash_password(password: str) -> str:
        """Transforms password from it's raw textual form to
        cryptographic hashes
        """
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode('utf-8')

    def validate_password(self, password: str) -> bool:
        """Confirms password validity"""
        return bcrypt.checkpw(password.encode(), self.hashed_password.encode())

    def generate_token(self) -> dict[str, str]:
        """Generates JWT token"""
        payload: dict[str, Any] = {
            'user_id': str(self.id),
            'exp': datetime.now(timezone.utc)
            + timedelta(minutes=settings.access_token_expire_minutes),
        }
        token: str = jwt.encode(
            claims=payload,
            key=settings.secret_key,
            algorithm=settings.algorithm
        )
        return {'access_token': token}
