"""Paper chunk model for storing text chunks with embeddings."""
from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime

from app.db.base_class import Base


class PaperChunk(Base):
    """Model for storing paper chunks with embeddings."""
    __tablename__ = "paper_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    
    # Chunk content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Position in the paper (0-based)
    start_char = Column(Integer, nullable=False)  # Starting character position in full text
    end_char = Column(Integer, nullable=False)    # Ending character position in full text
    word_count = Column(Integer, nullable=False)
    
    # Embedding
    embedding = Column(Vector(384))  # 384 dimensions for all-MiniLM-L6-v2
    
    # Metadata
    section_title = Column(String(255))  # E.g., "Introduction", "Methods", etc.
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    paper = relationship("Paper", back_populates="chunks")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_paper_chunks_paper_id', 'paper_id'),
        Index('idx_paper_chunks_embedding', 'embedding', postgresql_using='ivfflat'),
    )