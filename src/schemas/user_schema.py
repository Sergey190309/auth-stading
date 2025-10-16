from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class BaseUserSchema(BaseModel):
    email: EmailStr = Field(...)
    full_name: str | None = Field(default=None)


class CreateUserSchema(BaseUserSchema):
    hashed_password: str = Field(..., alias='password')


class UserSchema(BaseUserSchema):
    id: UUID = Field(...)
    is_active: bool = Field(default=False)
    created_at: datetime = Field(..., description="Timestamp when user was created")

    model_config = ConfigDict(from_attributes=True)