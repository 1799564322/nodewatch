import uuid
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower()


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    role: Literal["admin", "viewer"]

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    user: UserResponse

