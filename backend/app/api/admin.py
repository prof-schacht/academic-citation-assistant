"""Admin API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import uuid

from app.db.session import get_db
from app.services.admin import AdminService


router = APIRouter()


# Temporary function to get current user ID - will be replaced with proper auth
async def get_current_user_id() -> uuid.UUID:
    """Get current user ID (temporary implementation)."""
    # For now, return a fixed UUID for testing
    # In production, this would validate JWT and return the actual user ID
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


class CleanDocumentsRequest(BaseModel):
    """Request to clean all documents."""
    confirmation: str  # Must be "DELETE ALL"


class CleanDocumentsResponse(BaseModel):
    """Response after cleaning documents."""
    documents_deleted: int
    citations_deleted: int
    document_papers_deleted: int


@router.post("/clean-documents", response_model=CleanDocumentsResponse)
async def clean_all_documents(
    request: CleanDocumentsRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Delete all documents from all users (admin only)."""
    # Verify confirmation text
    if request.confirmation != "DELETE ALL":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid confirmation. Please type 'DELETE ALL' to confirm.",
        )
    
    # In production, check if user is admin
    # For now, we'll allow any authenticated user
    
    result = await AdminService.clean_all_documents(db)
    
    return CleanDocumentsResponse(**result)