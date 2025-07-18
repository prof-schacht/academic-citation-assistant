#!/usr/bin/env python3
"""Robust PDF processing script that handles errors gracefully."""
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_, or_
from app.models import Paper
from app.services.paper_processor import PaperProcessorService
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def process_papers_batch():
    """Process unprocessed papers in small batches."""
    engine = create_async_engine("postgresql+asyncpg://citation_user:citation_pass@localhost:5432/citation_db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    batch_size = 5  # Process 5 papers at a time
    
    async with async_session() as db:
        try:
            # Get unprocessed papers (excluding those with errors)
            result = await db.execute(
                select(Paper).where(
                    and_(
                        Paper.file_path.isnot(None),
                        Paper.is_processed == False,
                        or_(
                            Paper.processing_error.is_(None),
                            Paper.processing_error == ""
                        )
                    )
                ).limit(batch_size)
            )
            papers = result.scalars().all()
            
            if not papers:
                # Try papers with errors (retry)
                result = await db.execute(
                    select(Paper).where(
                        and_(
                            Paper.file_path.isnot(None),
                            Paper.is_processed == False
                        )
                    ).limit(batch_size)
                )
                papers = result.scalars().all()
                
                if not papers:
                    logger.info("No more papers to process!")
                    return 0
            
            logger.info(f"Processing batch of {len(papers)} papers...")
            
            success_count = 0
            
            for paper in papers:
                try:
                    # Clear previous error
                    paper.processing_error = None
                    await db.commit()
                    
                    logger.info(f"Processing: {paper.title[:60]}...")
                    
                    # Check file exists
                    if not os.path.exists(paper.file_path):
                        logger.error(f"File not found: {paper.file_path}")
                        paper.processing_error = "File not found"
                        continue
                    
                    # Process the paper
                    await PaperProcessorService.process_paper(
                        paper_id=str(paper.id),
                        file_path=paper.file_path
                    )
                    
                    success_count += 1
                    logger.info(f"✅ Successfully processed: {paper.title[:60]}")
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"❌ Error processing {paper.title[:30]}: {error_msg}")
                    paper.processing_error = error_msg[:500]  # Truncate long errors
                    
                await db.commit()
            
            logger.info(f"Batch complete: {success_count}/{len(papers)} successful")
            await engine.dispose()
            return len(papers)
            
        except Exception as e:
            logger.error(f"Fatal error in batch processing: {e}")
            await engine.dispose()
            return 0

async def main():
    """Main processing loop."""
    logger.info("=== STARTING ROBUST PDF PROCESSING ===")
    
    total_processed = 0
    
    while True:
        # Process a batch
        processed = await process_papers_batch()
        
        if processed == 0:
            break
            
        total_processed += processed
        logger.info(f"Total processed so far: {total_processed}")
        
        # Small delay between batches
        await asyncio.sleep(2)
    
    logger.info(f"=== PROCESSING COMPLETE: {total_processed} papers ===")

if __name__ == "__main__":
    asyncio.run(main())