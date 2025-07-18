"""Pydantic schemas for system logs."""
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.system_log import LogLevel, LogCategory


class SystemLogBase(BaseModel):
    """Base schema for system logs."""
    level: LogLevel
    category: LogCategory
    message: str
    details: Optional[Dict[str, Any]] = None
    error_trace: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None


class SystemLogCreate(SystemLogBase):
    """Schema for creating a system log."""
    user_id: Optional[UUID] = None


class SystemLogUpdate(BaseModel):
    """Schema for updating a system log (typically not used)."""
    pass


class SystemLogInDBBase(SystemLogBase):
    """Base schema for system logs in database."""
    id: UUID
    created_at: datetime
    user_id: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class SystemLog(SystemLogInDBBase):
    """Schema for system log with minimal user info."""
    user_email: Optional[str] = None


class SystemLogInDB(SystemLogInDBBase):
    """Schema for system log in database."""
    pass


class SystemLogFilter(BaseModel):
    """Schema for filtering system logs."""
    level: Optional[LogLevel] = None
    category: Optional[LogCategory] = None
    user_id: Optional[UUID] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search: Optional[str] = Field(None, description="Search in message field")


class SystemLogList(BaseModel):
    """Schema for paginated system log list."""
    logs: List[SystemLog]
    total: int
    page: int = Field(ge=1)
    per_page: int = Field(ge=1, le=100)
    total_pages: int