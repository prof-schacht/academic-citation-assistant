"""User schemas."""
from typing import Optional
from datetime import datetime
import uuid

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = None
    affiliation: Optional[str] = Field(None, max_length=255)


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = None
    affiliation: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, min_length=8)


class UserInDB(UserBase):
    """User schema with database fields."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    is_active: bool = True
    is_verified: bool = False
    is_superuser: bool = False
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None


class User(UserInDB):
    """User schema for API responses."""
    pass