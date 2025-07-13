"""Document model."""
import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING, Optional, Dict, Any

from sqlalchemy import String, DateTime, ForeignKey, JSON, Text, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.citation import Citation


class Document(Base):
    """Document model for user papers and writings."""
    
    __tablename__ = "documents"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Document metadata
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Content - stored as Lexical editor JSON format
    content: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    plain_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # For search and analysis
    
    # Document stats
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    citation_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Sharing and permissions
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    share_token: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_accessed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="documents")
    citations: Mapped[List["Citation"]] = relationship("Citation", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title={self.title})>"