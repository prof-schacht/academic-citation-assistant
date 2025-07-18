"""Test PDF processing functionality during Zotero sync."""
import asyncio
import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.models import User, Paper, PaperChunk, ZoteroSync
from app.services.zotero_service import ZoteroService
from app.services.paper_processor import PaperProcessorService


class PDFProcessingTester:
    """Test PDF processing during sync."""
    
    def __init__(self):
        self.engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=False)
        self.SessionLocal = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
    async def test_paper_processing_status(self, user_email: str = "zotero_test@example.com"):
        """Check the processing status of all papers."""
        async with self.SessionLocal() as session:
            # Get user
            result = await session.execute(
                select(User).where(User.email == user_email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.error(f"User {user_email} not found")
                return
                
            # Get all papers synced by this user
            result = await session.execute(
                select(Paper)
                .join(ZoteroSync)
                .where(ZoteroSync.user_id == user.id)
                .order_by(Paper.created_at.desc())
            )
            papers = result.scalars().all()
            
            logger.info(f"\n{'='*60}")
            logger.info(f"PAPER PROCESSING STATUS")
            logger.info(f"{'='*60}\n")
            
            logger.info(f"Total papers synced: {len(papers)}")
            
            # Categorize papers
            processed_papers = []
            unprocessed_papers = []
            papers_with_errors = []
            papers_without_files = []
            
            for paper in papers:
                if not paper.file_path:
                    papers_without_files.append(paper)
                elif paper.is_processed:
                    processed_papers.append(paper)
                elif paper.processing_error:
                    papers_with_errors.append(paper)
                else:
                    unprocessed_papers.append(paper)
                    
            # Display statistics
            logger.info(f"\nStatistics:")
            logger.info(f"  Successfully processed: {len(processed_papers)}")
            logger.info(f"  Without PDF files: {len(papers_without_files)}")
            logger.info(f"  Processing errors: {len(papers_with_errors)}")
            logger.info(f"  Not processed yet: {len(unprocessed_papers)}")
            
            # Show details for each category
            if processed_papers:
                logger.info(f"\n✓ Successfully Processed Papers ({len(processed_papers)}):")
                for paper in processed_papers[:5]:  # Show first 5
                    # Count chunks
                    result = await session.execute(
                        select(PaperChunk).where(PaperChunk.paper_id == paper.id)
                    )
                    chunks = result.scalars().all()
                    logger.info(f"  - {paper.title[:60]}... ({len(chunks)} chunks)")
                    
            if papers_without_files:
                logger.info(f"\n⚠ Papers Without PDFs ({len(papers_without_files)}):")
                for paper in papers_without_files[:5]:
                    logger.info(f"  - {paper.title[:60]}...")
                    
            if papers_with_errors:
                logger.error(f"\n✗ Papers With Processing Errors ({len(papers_with_errors)}):")
                for paper in papers_with_errors[:5]:
                    logger.error(f"  - {paper.title[:60]}...")
                    logger.error(f"    Error: {paper.processing_error}")
                    
            if unprocessed_papers:
                logger.warning(f"\n⏳ Unprocessed Papers ({len(unprocessed_papers)}):")
                for paper in unprocessed_papers[:5]:
                    logger.warning(f"  - {paper.title[:60]}...")
                    logger.warning(f"    File: {paper.file_path}")
                    
    async def process_unprocessed_papers(self, user_email: str = "zotero_test@example.com"):
        """Process any unprocessed papers."""
        async with self.SessionLocal() as session:
            # Get user
            result = await session.execute(
                select(User).where(User.email == user_email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.error(f"User {user_email} not found")
                return
                
            # Get unprocessed papers with files
            result = await session.execute(
                select(Paper)
                .join(ZoteroSync)
                .where(
                    ZoteroSync.user_id == user.id,
                    Paper.file_path.isnot(None),
                    Paper.is_processed == False,
                    Paper.processing_error.is_(None)
                )
            )
            unprocessed_papers = result.scalars().all()
            
            if not unprocessed_papers:
                logger.info("No unprocessed papers found.")
                return
                
            logger.info(f"\n{'='*60}")
            logger.info(f"PROCESSING {len(unprocessed_papers)} UNPROCESSED PAPERS")
            logger.info(f"{'='*60}\n")
            
            for i, paper in enumerate(unprocessed_papers):
                logger.info(f"\n[{i+1}/{len(unprocessed_papers)}] Processing: {paper.title[:60]}...")
                logger.info(f"  File: {paper.file_path}")
                
                try:
                    # Process the paper
                    await PaperProcessorService.process_paper(
                        str(paper.id),
                        paper.file_path
                    )
                    logger.info(f"  ✓ Successfully processed")
                    
                    # Verify chunks were created
                    await session.refresh(paper)
                    result = await session.execute(
                        select(PaperChunk).where(PaperChunk.paper_id == paper.id)
                    )
                    chunks = result.scalars().all()
                    logger.info(f"  Created {len(chunks)} chunks")
                    
                except Exception as e:
                    logger.error(f"  ✗ Processing failed: {e}")
                    paper.processing_error = str(e)
                    paper.is_processed = False
                    await session.commit()
                    
    async def verify_embeddings(self, user_email: str = "zotero_test@example.com"):
        """Verify that embeddings were generated for processed papers."""
        async with self.SessionLocal() as session:
            # Get user
            result = await session.execute(
                select(User).where(User.email == user_email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.error(f"User {user_email} not found")
                return
                
            # Get processed papers
            result = await session.execute(
                select(Paper)
                .join(ZoteroSync)
                .where(
                    ZoteroSync.user_id == user.id,
                    Paper.is_processed == True
                )
            )
            papers = result.scalars().all()
            
            logger.info(f"\n{'='*60}")
            logger.info(f"EMBEDDING VERIFICATION")
            logger.info(f"{'='*60}\n")
            
            papers_with_embeddings = 0
            papers_without_embeddings = 0
            total_chunks_with_embeddings = 0
            total_chunks_without_embeddings = 0
            
            for paper in papers:
                # Check paper embedding
                if paper.embedding is not None:
                    papers_with_embeddings += 1
                else:
                    papers_without_embeddings += 1
                    
                # Check chunk embeddings
                result = await session.execute(
                    select(PaperChunk).where(PaperChunk.paper_id == paper.id)
                )
                chunks = result.scalars().all()
                
                chunks_with_embeddings = sum(1 for c in chunks if c.embedding is not None)
                chunks_without_embeddings = len(chunks) - chunks_with_embeddings
                
                total_chunks_with_embeddings += chunks_with_embeddings
                total_chunks_without_embeddings += chunks_without_embeddings
                
                if chunks_without_embeddings > 0:
                    logger.warning(f"Paper '{paper.title[:50]}...' has {chunks_without_embeddings} chunks without embeddings")
                    
            logger.info(f"\nSummary:")
            logger.info(f"  Papers with embeddings: {papers_with_embeddings}/{len(papers)}")
            logger.info(f"  Papers without embeddings: {papers_without_embeddings}")
            logger.info(f"  Total chunks with embeddings: {total_chunks_with_embeddings}")
            logger.info(f"  Total chunks without embeddings: {total_chunks_without_embeddings}")
            
    async def cleanup(self):
        """Clean up resources."""
        await self.engine.dispose()


async def main():
    """Run PDF processing tests."""
    tester = PDFProcessingTester()
    
    try:
        # Test 1: Check current processing status
        await tester.test_paper_processing_status()
        
        # Test 2: Process any unprocessed papers
        await tester.process_unprocessed_papers()
        
        # Test 3: Verify embeddings
        await tester.verify_embeddings()
        
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())