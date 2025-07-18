"""Paper schemas for API requests and responses."""
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class PaperBase(BaseModel):
    """Base paper schema."""
    title: str = Field(..., max_length=1000)
    authors: Optional[List[str]] = None
    abstract: Optional[str] = None
    year: Optional[int] = Field(None, ge=1900, le=2100)
    journal: Optional[str] = Field(None, max_length=500)
    doi: Optional[str] = Field(None, max_length=200)
    arxiv_id: Optional[str] = Field(None, max_length=100)
    pubmed_id: Optional[str] = Field(None, max_length=100)
    semantic_scholar_id: Optional[str] = Field(None, max_length=100)


class PaperCreate(PaperBase):
    """Schema for creating a paper."""
    pass


class PaperUpdate(BaseModel):
    """Schema for updating a paper."""
    title: Optional[str] = Field(None, max_length=1000)
    authors: Optional[List[str]] = None
    abstract: Optional[str] = None
    year: Optional[int] = Field(None, ge=1900, le=2100)
    journal: Optional[str] = Field(None, max_length=500)
    doi: Optional[str] = Field(None, max_length=200)


class PaperResponse(PaperBase):
    """Schema for paper response."""
    id: UUID
    citation_count: int = 0
    reference_count: int = 0
    source: Optional[str] = None
    is_processed: bool = False
    processing_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Additional fields for frontend
    status: str = Field(description="Computed status: indexed, processing, or error")
    chunk_count: Optional[int] = Field(None, description="Number of text chunks if processed")
    has_pdf: bool = Field(False, description="Whether this paper has a PDF file available")
    
    class Config:
        from_attributes = True


class PaperListResponse(BaseModel):
    """Schema for paginated paper list response."""
    papers: List[PaperResponse]
    total: int
    skip: int
    limit: int