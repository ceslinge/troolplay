from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)


class MeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str
    role: str
    created_at: datetime


class SignupIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    accept_rules: Literal[True]
    age_confirmed: Literal[True]


class TokenIn(BaseModel):
    token: str = Field(max_length=100)


class EmailIn(BaseModel):
    email: EmailStr


class Message(BaseModel):
    detail: str
