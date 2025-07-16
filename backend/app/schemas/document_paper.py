"""Schemas for document-paper assignments."""
from typing import Optional, List
from datetime import datetime
import uuid

from pydantic import BaseModel, Field


class SimplePaperResponse(BaseModel):
    """Simplified paper response for document-paper assignments."""
    id: uuid.UUID
    title: str
    authors: Optional[List[str]] = None
    year: Optional[int] = None
    journal: Optional[str] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    
    class Config:
        from_attributes = True


class DocumentPaperBase(BaseModel):
    """Base schema for document-paper assignment."""
    notes: Optional[str] = Field(None, description="Notes about this paper in the context of this document")


class DocumentPaperCreate(DocumentPaperBase):
    """Schema for creating a document-paper assignment."""
    paper_id: uuid.UUID = Field(..., description="ID of the paper to assign")
    position: Optional[int] = Field(None, description="Position in bibliography (auto-assigned if not provided)")


class DocumentPaperUpdate(BaseModel):
    """Schema for updating a document-paper assignment."""
    notes: Optional[str] = Field(None, description="Updated notes")
    position: Optional[int] = Field(None, description="Updated position")


class DocumentPaperBulkAssign(BaseModel):
    """Schema for bulk assigning papers to a document."""
    paper_ids: List[uuid.UUID] = Field(..., description="List of paper IDs to assign")


class DocumentPaperReorder(BaseModel):
    """Schema for reordering papers in a document."""
    paper_ids: List[uuid.UUID] = Field(..., description="Ordered list of paper IDs")


class DocumentPaperResponse(DocumentPaperBase):
    """Response schema for document-paper assignment."""
    id: uuid.UUID
    document_id: uuid.UUID
    paper_id: uuid.UUID
    position: int
    added_at: datetime
    added_by: Optional[uuid.UUID]
    paper: SimplePaperResponse
    
    class Config:
        from_attributes = True