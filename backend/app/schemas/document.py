"""Document schemas."""
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from pydantic import BaseModel, Field, ConfigDict


class DocumentBase(BaseModel):
    """Base document schema."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=1000)
    content: Optional[Dict[str, Any]] = None
    is_public: bool = False


class DocumentCreate(DocumentBase):
    """Schema for creating a document."""
    pass


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=1000)
    content: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None


class DocumentInDB(DocumentBase):
    """Document schema with database fields."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    owner_id: uuid.UUID
    plain_text: Optional[str] = None
    word_count: int = 0
    citation_count: int = 0
    share_token: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_accessed_at: datetime


class Document(DocumentInDB):
    """Document schema for API responses."""
    pass


class DocumentList(BaseModel):
    """Schema for document list response."""
    documents: list[Document]
    total: int
    page: int
    pages: int
    limit: int