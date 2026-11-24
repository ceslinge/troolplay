from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# La règle d'un nouveau mot de passe, partagée par l'inscription et les changements.
NewPassword = Annotated[str, Field(min_length=10, max_length=128)]


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)


class MeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str
    role: str
    created_at: datetime
    capabilities: list[str]


class SignupIn(BaseModel):
    email: EmailStr
    password: NewPassword
    accept_rules: Literal[True]
    age_confirmed: Literal[True]


class TokenIn(BaseModel):
    token: str = Field(max_length=100)


class EmailIn(BaseModel):
    email: EmailStr


class Message(BaseModel):
    detail: str


class PasswordResetIn(BaseModel):
    token: str = Field(max_length=100)
    password: NewPassword


class PasswordChangeIn(BaseModel):
    current_password: str = Field(max_length=128)
    new_password: NewPassword


class AccountDeletionIn(BaseModel):
    password: str = Field(max_length=128)
