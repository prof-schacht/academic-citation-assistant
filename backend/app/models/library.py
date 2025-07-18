"""Library model."""
import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING, Optional

from sqlalchemy import String, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.paper import Paper


class Library(Base):
    """Library model for organizing papers."""
    
    __tablename__ = "libraries"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Library metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Privacy settings
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    share_token: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="libraries")
    library_papers: Mapped[List["LibraryPaper"]] = relationship("LibraryPaper", back_populates="library", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Library(id={self.id}, name={self.name})>"


class LibraryPaper(Base):
    """Association table for library-paper many-to-many relationship with extra fields."""
    
    __tablename__ = "library_papers"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    library_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("libraries.id"), nullable=False)
    paper_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("papers.id"), nullable=False)
    
    # Additional metadata
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # List of tags for this paper in this library
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    library: Mapped["Library"] = relationship("Library", back_populates="library_papers")
    paper: Mapped["Paper"] = relationship("Paper", back_populates="library_papers")
    
    def __repr__(self) -> str:
        return f"<LibraryPaper(library_id={self.library_id}, paper_id={self.paper_id})>"