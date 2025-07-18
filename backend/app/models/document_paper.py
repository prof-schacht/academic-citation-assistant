"""Association table for document-paper relationships."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.paper import Paper


class DocumentPaper(Base):
    """Association between documents and papers for bibliography management."""
    
    __tablename__ = "document_papers"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("documents.id", ondelete="CASCADE"), 
        nullable=False
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("papers.id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # Metadata
    position: Mapped[int] = mapped_column(Integer, default=0)  # Order in bibliography
    notes: Mapped[str] = mapped_column(Text, nullable=True)  # User notes about this paper in context
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    added_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)  # User who added it
    
    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="document_papers")
    paper: Mapped["Paper"] = relationship("Paper", back_populates="document_papers")
    
    # Unique constraint to prevent duplicate assignments
    __table_args__ = (
        UniqueConstraint("document_id", "paper_id", name="uq_document_paper"),
    )
    
    def __repr__(self) -> str:
        return f"<DocumentPaper(document_id={self.document_id}, paper_id={self.paper_id})>"