"""System log model for tracking various system events."""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from enum import Enum

from sqlalchemy import String, DateTime, Text, JSON, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.user import User


class LogLevel(str, Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(str, Enum):
    """Log category enumeration."""
    ZOTERO_SYNC = "ZOTERO_SYNC"
    PDF_PROCESSING = "PDF_PROCESSING"
    SYSTEM = "SYSTEM"
    AUTH = "AUTH"
    API = "API"
    DATABASE = "DATABASE"
    SEARCH = "SEARCH"


class SystemLog(Base):
    """System log model for tracking application events."""
    
    __tablename__ = "system_logs"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Log fields
    level: Mapped[LogLevel] = mapped_column(SQLEnum(LogLevel), nullable=False, index=True)
    category: Mapped[LogCategory] = mapped_column(SQLEnum(LogCategory), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Additional context
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error_trace: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Related entity information
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    
    # User association (optional - some logs may be system-level)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"), 
        nullable=True,
        index=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", lazy="joined")
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_logs_created_level', 'created_at', 'level'),
        Index('idx_logs_category_created', 'category', 'created_at'),
        Index('idx_logs_user_created', 'user_id', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<SystemLog(id={self.id}, level={self.level}, category={self.category}, message={self.message[:50]}...)>"