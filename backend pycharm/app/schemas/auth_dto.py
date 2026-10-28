import re
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

EMAIL_REGEX = re.compile(r"^[\w\.-]+@([\w\.-]+\.)+[a-zA-Z]{2,}$")


class SignupRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: str = Field(..., description="Valid user email address")
    password: str = Field(..., min_length=6, max_length=128, description="Password (min 6 characters)")
    confirm_password: str = Field(..., description="Password confirmation")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Username cannot be blank")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip()
        if not EMAIL_REGEX.match(v):
            raise ValueError("Invalid email format (e.g. user@domain.com)")
        return v.lower()


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, description="Username or Email")
    password: str = Field(..., min_length=1, description="Password")


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str] = ""
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    message: str
