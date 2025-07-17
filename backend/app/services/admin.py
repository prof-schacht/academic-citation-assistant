"""Admin service for system management operations."""
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, func

from app.models.document import Document
from app.models.citation import Citation
from app.models.document_paper import DocumentPaper
from app.models.paper import Paper
from app.models.paper_chunk import PaperChunk
from app.models.system_log import SystemLog, LogLevel, LogCategory


class AdminService:
    """Service for admin operations."""
    
    @staticmethod
    async def clean_all_documents(db: AsyncSession) -> Dict[str, int]:
        """Delete all documents and related data from the database."""
        # Count existing records before deletion
        doc_count_query = select(func.count(Document.id))
        citation_count_query = select(func.count(Citation.id))
        doc_paper_count_query = select(func.count(DocumentPaper.id))
        
        doc_count_result = await db.execute(doc_count_query)
        doc_count = doc_count_result.scalar() or 0
        
        citation_count_result = await db.execute(citation_count_query)
        citation_count = citation_count_result.scalar() or 0
        
        doc_paper_count_result = await db.execute(doc_paper_count_query)
        doc_paper_count = doc_paper_count_result.scalar() or 0
        
        # Delete all documents (citations and document_papers will cascade)
        await db.execute(delete(Document))
        
        # Log the operation
        log_entry = SystemLog(
            level=LogLevel.WARNING,
            category=LogCategory.DATABASE,
            message="All documents cleaned from database",
            details={
                "documents_deleted": doc_count,
                "citations_deleted": citation_count,
                "document_papers_deleted": doc_paper_count,
            }
        )
        db.add(log_entry)
        
        await db.commit()
        
        return {
            "documents_deleted": doc_count,
            "citations_deleted": citation_count,
            "document_papers_deleted": doc_paper_count,
        }
    
    @staticmethod
    async def clean_all_papers(db: AsyncSession) -> Dict[str, int]:
        """Delete all papers and related data from the database."""
        # Count existing records before deletion
        paper_count_query = select(func.count(Paper.id))
        chunk_count_query = select(func.count(PaperChunk.id))
        
        paper_count_result = await db.execute(paper_count_query)
        paper_count = paper_count_result.scalar() or 0
        
        chunk_count_result = await db.execute(chunk_count_query)
        chunk_count = chunk_count_result.scalar() or 0
        
        # Delete all paper chunks first (foreign key constraint)
        await db.execute(delete(PaperChunk))
        
        # Delete all papers
        await db.execute(delete(Paper))
        
        # Log the operation
        log_entry = SystemLog(
            level=LogLevel.WARNING,
            category=LogCategory.DATABASE,
            message="All papers cleaned from database",
            details={
                "papers_deleted": paper_count,
                "chunks_deleted": chunk_count,
            }
        )
        db.add(log_entry)
        
        await db.commit()
        
        return {
            "papers_deleted": paper_count,
            "chunks_deleted": chunk_count,
        }