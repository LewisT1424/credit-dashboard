from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    PORTFOLIO_MANAGER = "portfolio_manager"


class UserBase(BaseModel):
    """Base user schema with common attributes."""
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=255)
    role: UserRole = UserRole.PORTFOLIO_MANAGER


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8, max_length=100)
    
    @validator('password')
    def password_strength(cls, v):
        """Validate password strength."""
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        return v


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """Schema for user as stored in database."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class User(UserInDB):
    """Schema for user response (excludes sensitive data)."""
    pass


class Token(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User


class TokenData(BaseModel):
    """Schema for decoded token data."""
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    """Schema for login request."""
    username: str
    password: str
