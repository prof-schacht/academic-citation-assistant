"""Document API endpoints."""
from typing import Optional
import uuid
import math
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.document import (
    Document, DocumentCreate, DocumentUpdate, DocumentList
)
from app.services.document import DocumentService


router = APIRouter()


# Temporary function to get current user ID - will be replaced with proper auth
async def get_current_user_id() -> uuid.UUID:
    """Get current user ID (temporary implementation)."""
    # For now, return a fixed UUID for testing
    # In production, this would validate JWT and return the actual user ID
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.post("/", response_model=Document, status_code=status.HTTP_201_CREATED)
async def create_document(
    document_data: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Create a new document."""
    document = await DocumentService.create_document(db, document_data, user_id)
    return document


@router.get("/", response_model=DocumentList)
async def list_documents(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    public_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """List documents with pagination."""
    skip = (page - 1) * limit
    
    documents, total = await DocumentService.get_documents(
        db=db,
        user_id=user_id if not public_only else None,
        skip=skip,
        limit=limit,
        search=search,
        is_public_only=public_only,
    )
    
    pages = math.ceil(total / limit)
    
    return DocumentList(
        documents=documents,
        total=total,
        page=page,
        pages=pages,
        limit=limit,
    )


@router.get("/{document_id}", response_model=Document)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get a specific document."""
    document = await DocumentService.get_document(db, document_id, user_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    return document


@router.get("/share/{share_token}", response_model=Document)
async def get_document_by_share_token(
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a public document by share token."""
    from sqlalchemy import select
    from app.models.document import Document as DocumentModel
    
    query = select(DocumentModel).where(
        (DocumentModel.share_token == share_token) & 
        (DocumentModel.is_public == True)
    )
    result = await db.execute(query)
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Update last accessed timestamp
    document.last_accessed_at = datetime.utcnow()
    await db.commit()
    
    return document


@router.put("/{document_id}", response_model=Document)
async def update_document(
    document_id: uuid.UUID,
    document_data: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Update a document."""
    document = await DocumentService.update_document(
        db, document_id, document_data, user_id
    )
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or you don't have permission to update it",
        )
    
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Delete a document."""
    deleted = await DocumentService.delete_document(db, document_id, user_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or you don't have permission to delete it",
        )
    
    return None