"""API endpoints for document-paper assignments."""
from typing import List, Optional
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.user import User
from app.models.document import Document
from app.models.paper import Paper
from app.models.document_paper import DocumentPaper
from app.api.deps import get_current_user
from app.schemas.document_paper import (
    DocumentPaperCreate,
    DocumentPaperUpdate,
    DocumentPaperResponse,
    DocumentPaperBulkAssign,
    DocumentPaperReorder
)

router = APIRouter()


@router.post("/documents/{document_id}/papers", response_model=DocumentPaperResponse)
async def assign_paper_to_document(
    document_id: uuid.UUID,
    paper_assignment: DocumentPaperCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DocumentPaperResponse:
    """Assign a paper to a document's bibliography."""
    # Verify document exists and user has access
    result = await db.execute(
        select(Document).where(
            and_(
                Document.id == document_id,
                Document.owner_id == current_user.id
            )
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Verify paper exists
    result = await db.execute(
        select(Paper).where(Paper.id == paper_assignment.paper_id)
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Check if already assigned
    result = await db.execute(
        select(DocumentPaper).where(
            and_(
                DocumentPaper.document_id == document_id,
                DocumentPaper.paper_id == paper_assignment.paper_id
            )
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Paper already assigned to this document")
    
    # Get the next position
    result = await db.execute(
        select(func.max(DocumentPaper.position)).where(
            DocumentPaper.document_id == document_id
        )
    )
    max_position = result.scalar() or -1
    
    # Create assignment
    doc_paper = DocumentPaper(
        document_id=document_id,
        paper_id=paper_assignment.paper_id,
        position=paper_assignment.position if paper_assignment.position is not None else max_position + 1,
        notes=paper_assignment.notes,
        added_by=current_user.id
    )
    
    db.add(doc_paper)
    await db.commit()
    
    # Reload with paper relationship
    result = await db.execute(
        select(DocumentPaper)
        .options(selectinload(DocumentPaper.paper))
        .where(DocumentPaper.id == doc_paper.id)
    )
    doc_paper = result.scalar_one()
    
    # TODO: Add logging
    
    return doc_paper


@router.post("/documents/{document_id}/papers/bulk", response_model=List[DocumentPaperResponse])
async def bulk_assign_papers(
    document_id: uuid.UUID,
    bulk_assignment: DocumentPaperBulkAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[DocumentPaperResponse]:
    """Bulk assign multiple papers to a document."""
    # Verify document exists and user has access
    result = await db.execute(
        select(Document).where(
            and_(
                Document.id == document_id,
                Document.owner_id == current_user.id
            )
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Verify all papers exist
    result = await db.execute(
        select(Paper).where(Paper.id.in_(bulk_assignment.paper_ids))
    )
    papers = result.scalars().all()
    if len(papers) != len(bulk_assignment.paper_ids):
        raise HTTPException(status_code=400, detail="One or more papers not found")
    
    # Check for existing assignments
    result = await db.execute(
        select(DocumentPaper.paper_id).where(
            and_(
                DocumentPaper.document_id == document_id,
                DocumentPaper.paper_id.in_(bulk_assignment.paper_ids)
            )
        )
    )
    existing_paper_ids = {str(row) for row in result.scalars().all()}
    
    # Filter out already assigned papers
    new_paper_ids = [pid for pid in bulk_assignment.paper_ids if str(pid) not in existing_paper_ids]
    
    if not new_paper_ids:
        raise HTTPException(status_code=400, detail="All papers are already assigned to this document")
    
    # Get the next position
    result = await db.execute(
        select(func.max(DocumentPaper.position)).where(
            DocumentPaper.document_id == document_id
        )
    )
    max_position = result.scalar() or -1
    
    # Create assignments
    doc_papers = []
    for i, paper_id in enumerate(new_paper_ids):
        doc_paper = DocumentPaper(
            document_id=document_id,
            paper_id=paper_id,
            position=max_position + 1 + i,
            added_by=current_user.id
        )
        db.add(doc_paper)
        doc_papers.append(doc_paper)
    
    await db.commit()
    
    # Reload all assignments with paper relationships
    result = await db.execute(
        select(DocumentPaper)
        .options(selectinload(DocumentPaper.paper))
        .where(
            and_(
                DocumentPaper.document_id == document_id,
                DocumentPaper.paper_id.in_(new_paper_ids)
            )
        )
        .order_by(DocumentPaper.position)
    )
    doc_papers = result.scalars().all()
    
    # TODO: Add logging
    
    return doc_papers


@router.get("/documents/{document_id}/papers", response_model=List[DocumentPaperResponse])
async def get_document_papers(
    document_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[DocumentPaperResponse]:
    """Get all papers assigned to a document."""
    # Verify document exists and user has access
    result = await db.execute(
        select(Document).where(
            and_(
                Document.id == document_id,
                Document.owner_id == current_user.id
            )
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get assigned papers
    result = await db.execute(
        select(DocumentPaper)
        .options(selectinload(DocumentPaper.paper))
        .where(DocumentPaper.document_id == document_id)
        .order_by(DocumentPaper.position)
        .offset(skip)
        .limit(limit)
    )
    doc_papers = result.scalars().all()
    
    return doc_papers


@router.patch("/documents/{document_id}/papers/{paper_id}", response_model=DocumentPaperResponse)
async def update_paper_assignment(
    document_id: uuid.UUID,
    paper_id: uuid.UUID,
    update_data: DocumentPaperUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DocumentPaperResponse:
    """Update a paper assignment (notes, position, etc)."""
    # Get the assignment
    result = await db.execute(
        select(DocumentPaper)
        .options(selectinload(DocumentPaper.paper))
        .join(Document)
        .where(
            and_(
                DocumentPaper.document_id == document_id,
                DocumentPaper.paper_id == paper_id,
                Document.owner_id == current_user.id
            )
        )
    )
    doc_paper = result.scalar_one_or_none()
    if not doc_paper:
        raise HTTPException(status_code=404, detail="Paper assignment not found")
    
    # Update fields
    if update_data.notes is not None:
        doc_paper.notes = update_data.notes
    if update_data.position is not None:
        doc_paper.position = update_data.position
    
    await db.commit()
    
    # Reload with paper relationship
    result = await db.execute(
        select(DocumentPaper)
        .options(selectinload(DocumentPaper.paper))
        .where(
            and_(
                DocumentPaper.document_id == document_id,
                DocumentPaper.paper_id == paper_id
            )
        )
    )
    doc_paper = result.scalar_one()
    
    return doc_paper


@router.post("/documents/{document_id}/papers/reorder")
async def reorder_papers(
    document_id: uuid.UUID,
    reorder_data: DocumentPaperReorder,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Reorder papers in a document's bibliography."""
    # Verify document exists and user has access
    result = await db.execute(
        select(Document).where(
            and_(
                Document.id == document_id,
                Document.owner_id == current_user.id
            )
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get all assignments for the document
    result = await db.execute(
        select(DocumentPaper).where(
            DocumentPaper.document_id == document_id
        )
    )
    doc_papers = {str(dp.paper_id): dp for dp in result.scalars().all()}
    
    # Verify all paper IDs exist
    for paper_id in reorder_data.paper_ids:
        if str(paper_id) not in doc_papers:
            raise HTTPException(status_code=400, detail=f"Paper {paper_id} not found in document")
    
    # Update positions
    for i, paper_id in enumerate(reorder_data.paper_ids):
        doc_papers[str(paper_id)].position = i
    
    await db.commit()
    
    # TODO: Add logging
    
    return {"message": "Papers reordered successfully"}


@router.delete("/documents/{document_id}/papers/{paper_id}")
async def remove_paper_from_document(
    document_id: uuid.UUID,
    paper_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Remove a paper from a document's bibliography."""
    # Get the assignment
    result = await db.execute(
        select(DocumentPaper)
        .join(Document)
        .where(
            and_(
                DocumentPaper.document_id == document_id,
                DocumentPaper.paper_id == paper_id,
                Document.owner_id == current_user.id
            )
        )
    )
    doc_paper = result.scalar_one_or_none()
    if not doc_paper:
        raise HTTPException(status_code=404, detail="Paper assignment not found")
    
    # Delete the assignment
    await db.delete(doc_paper)
    await db.commit()
    
    # TODO: Add logging
    
    return {"message": "Paper removed from document successfully"}