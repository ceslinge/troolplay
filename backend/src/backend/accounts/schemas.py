from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)


class MeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str
    role: str
    created_at: datetime
