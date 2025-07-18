"""Citation model."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional, Dict, Any

from sqlalchemy import String, DateTime, ForeignKey, Float, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.paper import Paper


class Citation(Base):
    """Citation model linking documents to papers."""
    
    __tablename__ = "citations"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    paper_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("papers.id"), nullable=False)
    
    # Citation metadata
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 to 1.0
    relevance_explanation: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Position in document
    position: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)  # {paragraph: int, sentence: int, offset: int}
    context_before: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    context_after: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Citation style
    citation_style: Mapped[str] = mapped_column(String(20), default="apa", nullable=False)
    citation_text: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Usage tracking
    times_viewed: Mapped[int] = mapped_column(Integer, default=0)
    times_exported: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="citations")
    paper: Mapped["Paper"] = relationship("Paper", back_populates="citations")
    
    def __repr__(self) -> str:
        return f"<Citation(id={self.id}, confidence={self.confidence_score})>"