from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User role enum defining access levels"""
    ADMIN = "admin"
    RESEARCHER = "researcher"
    VIEWER = "viewer"


class UserBase(BaseModel):
    """Base user model with common fields"""
    email: EmailStr
    full_name: str
    organization: Optional[str] = None
    role: UserRole = UserRole.RESEARCHER
    is_active: bool = True


class UserCreate(UserBase):
    """Model for creating a new user with password"""
    password: str


class UserUpdate(BaseModel):
    """Model for updating user information"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    organization: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserInDB(UserBase):
    """Internal user model with hashed password"""
    id: str
    hashed_password: str
    created_at: datetime
    updated_at: datetime


class User(UserBase):
    """User model returned to clients (without sensitive data)"""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class Token(BaseModel):
    """JWT token model"""
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class TokenData(BaseModel):
    """Data extracted from JWT token"""
    user_id: str
    role: UserRole
    exp: datetime 