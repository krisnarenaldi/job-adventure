from __future__ import annotations
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Optional
from app.models.user import UserRole
import uuid


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.RECRUITER

    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    password: str
    company_name: Optional[str] = None
    
    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    company_id: Optional[uuid.UUID] = None
    is_active: Optional[str] = None


class UserInDB(UserBase):
    id: uuid.UUID
    company_id: Optional[uuid.UUID] = None
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserInDB):
    pass


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse