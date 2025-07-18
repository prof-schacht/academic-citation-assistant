"""Paper upload and management endpoints."""
import os
import hashlib
from typing import List, Optional
from uuid import UUID
import aiofiles
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, String
from markitdown import MarkItDown

from app.db.session import get_db
from app.models import Paper, User
from app.schemas.paper import PaperCreate, PaperUpdate, PaperResponse, PaperListResponse
from app.services.paper_processor import PaperProcessorService
from app.services.background_processor import background_processor
from app.core.config import settings

router = APIRouter(prefix="/papers", tags=["papers"])

# Initialize MarkItDown for text extraction
markitdown = MarkItDown()

# File upload settings from Issue #6
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.rtf'}
UPLOAD_DIR = settings.upload_dir


def paper_to_response(paper: Paper, chunk_count: int = 0) -> PaperResponse:
    """Convert a Paper model to PaperResponse, handling computed fields."""
    return PaperResponse(
        # Copy all base fields
        id=paper.id,
        title=paper.title,
        authors=paper.authors,
        abstract=paper.abstract,
        year=paper.year,
        journal=paper.journal,
        doi=paper.doi,
        arxiv_id=paper.arxiv_id,
        pubmed_id=paper.pubmed_id,
        semantic_scholar_id=paper.semantic_scholar_id,
        citation_count=paper.citation_count,
        reference_count=paper.reference_count,
        source=paper.source,
        is_processed=paper.is_processed,
        processing_error=paper.processing_error,
        created_at=paper.created_at,
        updated_at=paper.updated_at,
        metadata_source=paper.metadata_source,
        # Computed fields
        status='indexed' if paper.is_processed else ('error' if paper.processing_error else 'processing'),
        chunk_count=chunk_count,
        has_pdf=paper.has_pdf
    )


@router.post("/upload", response_model=PaperResponse)
async def upload_paper(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a paper file for processing.
    
    Supported formats: PDF, DOCX, DOC, TXT, RTF
    Max file size: 50MB
    """
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_ext} not supported. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Validate file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds maximum of {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Calculate file hash for duplicate detection
    file_hash = hashlib.sha256(content).hexdigest()
    
    # Check for existing paper with same hash
    existing_paper = await db.execute(
        select(Paper).where(Paper.file_hash == file_hash)
    )
    existing_paper = existing_paper.scalar_one_or_none()
    
    if existing_paper:
        # Return existing paper if duplicate with status
        return paper_to_response(existing_paper, chunk_count=0)
    
    # Save file to disk
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, f"{file_hash}{file_ext}")
    
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    # Create paper record
    paper = Paper(
        title=file.filename,  # Temporary title, will be updated after processing
        source='upload',
        file_path=file_path,
        file_hash=file_hash,
        is_processed=False
    )
    
    db.add(paper)
    await db.commit()
    await db.refresh(paper)
    
    # Process paper in background
    background_tasks.add_task(
        PaperProcessorService.process_paper,
        paper_id=str(paper.id),
        file_path=file_path
    )
    
    # Return paper with status
    return paper_to_response(paper, chunk_count=0)


@router.get("/", response_model=PaperListResponse)
async def get_papers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = Query(None, regex="^(all|indexed|processing|error)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get all papers with optional filtering."""
    # Base query - get all papers for now (no user filtering)
    query = select(Paper)
    
    # Add search filter
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Paper.title.ilike(search_term),
                Paper.abstract.ilike(search_term),
                Paper.authors.cast(String).ilike(search_term)
            )
        )
    
    # Add status filter
    if status and status != 'all':
        if status == 'indexed':
            query = query.where(Paper.is_processed == True)
        elif status == 'processing':
            query = query.where(Paper.is_processed == False, Paper.processing_error.is_(None))
        elif status == 'error':
            query = query.where(Paper.processing_error.isnot(None))
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(Paper.created_at.desc())
    
    result = await db.execute(query)
    papers = result.scalars().all()
    
    # Transform papers to include status
    paper_responses = []
    for paper in papers:
        # For now, just estimate chunk count based on text length
        chunk_count = 0
        if paper.is_processed and paper.full_text:
            # Rough estimate: 500 words per chunk
            word_count = len(paper.full_text.split())
            chunk_count = max(1, word_count // 500)
        
        # Create response with computed fields
        paper_response = paper_to_response(paper, chunk_count=chunk_count)
        paper_responses.append(paper_response)
    
    return PaperListResponse(
        papers=paper_responses,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{paper_id}/chunks")
async def get_paper_chunks(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get all chunks for a paper with their content."""
    from app.models.paper_chunk import PaperChunk
    
    # Get the paper first
    paper = await db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get all chunks for this paper
    result = await db.execute(
        select(PaperChunk)
        .where(PaperChunk.paper_id == paper_id)
        .order_by(PaperChunk.chunk_index)
    )
    chunks = result.scalars().all()
    
    # Format the response
    chunks_data = [
        {
            "id": str(chunk.id),
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
            "start_char": chunk.start_char,
            "end_char": chunk.end_char,
            "word_count": chunk.word_count,
            "section_title": chunk.section_title
        }
        for chunk in chunks
    ]
    
    return {
        "paper_id": str(paper_id),
        "title": paper.title,
        "full_text": paper.full_text[:5000] if paper.full_text else None,  # First 5000 chars
        "full_text_length": len(paper.full_text) if paper.full_text else 0,
        "chunk_count": len(chunks),
        "chunks": chunks_data
    }


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific paper by ID."""
    paper = await db.get(Paper, paper_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Compute chunk count
    chunk_count = 0
    if paper.is_processed and paper.full_text:
        word_count = len(paper.full_text.split())
        chunk_count = max(1, word_count // 500)
    
    # Return with computed status
    return paper_to_response(paper, chunk_count=chunk_count)


@router.patch("/{paper_id}", response_model=PaperResponse)
async def update_paper(
    paper_id: UUID,
    paper_update: PaperUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update paper metadata."""
    paper = await db.get(Paper, paper_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Update fields
    update_data = paper_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(paper, field, value)
    
    await db.commit()
    await db.refresh(paper)
    
    # Compute chunk count
    chunk_count = 0
    if paper.is_processed and paper.full_text:
        word_count = len(paper.full_text.split())
        chunk_count = max(1, word_count // 500)
    
    # Return with computed status
    return paper_to_response(paper, chunk_count=chunk_count)


@router.delete("/{paper_id}")
async def delete_paper(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a paper and its associated data."""
    paper = await db.get(Paper, paper_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # TODO: Check if user has access to this paper
    
    # Delete file if it exists
    if paper.file_path and os.path.exists(paper.file_path):
        os.remove(paper.file_path)
    
    await db.delete(paper)
    await db.commit()
    
    return {"message": "Paper deleted successfully"}


@router.post("/{paper_id}/reprocess")
async def reprocess_paper(
    paper_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Reprocess a paper that failed or needs updating."""
    paper = await db.get(Paper, paper_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if not paper.file_path or not os.path.exists(paper.file_path):
        raise HTTPException(status_code=400, detail="Paper file not found")
    
    # Reset processing status
    paper.is_processed = False
    paper.processing_error = None
    await db.commit()
    
    # Reprocess in background
    background_tasks.add_task(
        PaperProcessorService.process_paper,
        paper_id=str(paper.id),
        file_path=paper.file_path
    )
    
    return {"message": "Paper queued for reprocessing"}


@router.get("/{paper_id}/pdf")
async def get_paper_pdf(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Download the PDF file for a paper."""
    paper = await db.get(Paper, paper_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if not paper.file_path:
        raise HTTPException(status_code=404, detail="No PDF available for this paper")
    
    # Ensure the file exists
    if not os.path.exists(paper.file_path):
        raise HTTPException(status_code=404, detail="PDF file not found on server")
    
    # Get the file extension to determine content type
    file_ext = os.path.splitext(paper.file_path)[1].lower()
    
    # Set appropriate content type
    content_type = "application/pdf" if file_ext == ".pdf" else "application/octet-stream"
    
    # Generate a safe filename for download
    safe_filename = f"{paper.title[:50].replace(' ', '_')}_{paper_id}{file_ext}"
    safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in ('_', '-', '.'))
    
    return FileResponse(
        path=paper.file_path,
        media_type=content_type,
        filename=safe_filename,
        headers={
            "Content-Disposition": f"inline; filename=\"{safe_filename}\"",
            "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
        }
    )


@router.get("/processing/status")
async def get_processing_status():
    """Get the status of the background processing queue."""
    status = await background_processor.get_queue_status()
    return status