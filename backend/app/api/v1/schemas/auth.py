import uuid

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    username: str = Field(min_length=2, max_length=20)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    username: str

    model_config = {"from_attributes": True}


class GoogleAuthRequest(BaseModel):
    code: str
    redirect_uri: str


class CsrfResponse(BaseModel):
    csrf_token: str
