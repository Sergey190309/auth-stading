from __future__ import annotations
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class BaseUserSchema(BaseModel):
    email: EmailStr = Field(...)
    full_name: str | None = Field(default=None)


class CreateUserSchema(BaseUserSchema):
    hashed_password: str = Field(..., alias='password')


class UserSchema(BaseUserSchema):
    id: UUID = Field(...)
    is_active: bool = Field(default=False)

    model_config = ConfigDict(from_attributes=True)