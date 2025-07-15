"""Paper model with vector support."""
import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
import numpy as np

from sqlalchemy import String, DateTime, Integer, Text, Float, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.core.config import settings

if TYPE_CHECKING:
    from app.models.citation import Citation
    from app.models.library import LibraryPaper
    from app.models.paper_chunk import PaperChunk
    from app.models.zotero_sync import ZoteroSync


class Paper(Base):
    """Paper model for academic papers with vector embeddings."""
    
    __tablename__ = "papers"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Paper metadata
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    authors: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # List of author names
    abstract: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Publication details
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    journal: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    doi: Mapped[Optional[str]] = mapped_column(String(200), unique=True, nullable=True, index=True)
    arxiv_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)
    pubmed_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)
    semantic_scholar_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)
    
    # Content and embeddings
    full_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    embedding: Mapped[Optional[np.ndarray]] = mapped_column(Vector(settings.embedding_dimension), nullable=True)
    
    # Paper statistics
    citation_count: Mapped[int] = mapped_column(Integer, default=0)
    reference_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Source information
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 'upload', 'semantic_scholar', 'arxiv', 'zotero', etc.
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Zotero-specific metadata
    zotero_key: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    
    # File information (if uploaded)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # SHA256 for duplicate detection
    
    # Processing status
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    citations: Mapped[List["Citation"]] = relationship("Citation", back_populates="paper", cascade="all, delete-orphan")
    library_papers: Mapped[List["LibraryPaper"]] = relationship("LibraryPaper", back_populates="paper", cascade="all, delete-orphan")
    chunks: Mapped[List["PaperChunk"]] = relationship("PaperChunk", back_populates="paper", cascade="all, delete-orphan")
    zotero_sync: Mapped[Optional["ZoteroSync"]] = relationship("ZoteroSync", back_populates="paper", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Paper(id={self.id}, title={self.title[:50]}...)>"