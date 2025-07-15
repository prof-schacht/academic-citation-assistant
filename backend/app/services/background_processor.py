"""Background PDF processor that runs automatically."""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
import threading
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Paper
from app.db.session import AsyncSessionLocal
from .paper_processor import PaperProcessorService

logger = logging.getLogger(__name__)


class BackgroundProcessor:
    """Handles background processing of PDFs."""
    
    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the background processor."""
        if self._running:
            logger.info("Background processor already running")
            return
            
        self._running = True
        logger.info("Starting background PDF processor")
        
        # Run in background
        self._task = asyncio.create_task(self._process_loop())
        
    async def stop(self):
        """Stop the background processor."""
        logger.info("Stopping background PDF processor")
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
                
    async def _process_loop(self):
        """Main processing loop."""
        while self._running:
            try:
                processed = await self._process_batch()
                
                if processed == 0:
                    # No papers to process, wait longer
                    await asyncio.sleep(60)  # Check every minute
                else:
                    # Processed some papers, check again soon
                    await asyncio.sleep(5)  # Short delay between batches
                    
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                await asyncio.sleep(30)  # Wait before retry
                
    async def _process_batch(self) -> int:
        """Process a batch of papers."""
        async with AsyncSessionLocal() as db:
            try:
                # Find unprocessed papers
                result = await db.execute(
                    select(Paper).where(
                        and_(
                            Paper.file_path.isnot(None),
                            Paper.is_processed == False,
                            or_(
                                Paper.processing_error.is_(None),
                                Paper.processing_error == "",
                                # Retry errors after 30 minutes
                                Paper.updated_at < datetime.utcnow() - timedelta(minutes=30)
                            )
                        )
                    ).limit(1)  # Process one at a time
                )
                
                paper = result.scalar_one_or_none()
                
                if not paper:
                    return 0
                    
                logger.info(f"Processing paper: {paper.title[:60]}...")
                
                try:
                    # Clear any previous error
                    paper.processing_error = None
                    await db.commit()
                    
                    # Process the paper
                    await PaperProcessorService.process_paper(
                        paper_id=str(paper.id),
                        file_path=paper.file_path
                    )
                    
                    logger.info(f"✅ Successfully processed: {paper.title[:60]}")
                    return 1
                    
                except Exception as e:
                    error_msg = str(e)[:500]
                    logger.error(f"❌ Failed to process {paper.title[:30]}: {error_msg}")
                    
                    paper.processing_error = error_msg
                    paper.updated_at = datetime.utcnow()
                    await db.commit()
                    
                    return 1  # Still counts as processed (with error)
                    
            except Exception as e:
                logger.error(f"Database error in batch processing: {e}")
                return 0
                
    async def get_queue_status(self) -> dict:
        """Get current queue status."""
        async with AsyncSessionLocal() as db:
            # Count papers
            total_papers = await db.execute(
                select(Paper).where(Paper.file_path.isnot(None))
            )
            total = len(total_papers.scalars().all())
            
            processed_papers = await db.execute(
                select(Paper).where(
                    and_(
                        Paper.file_path.isnot(None),
                        Paper.is_processed == True
                    )
                )
            )
            processed = len(processed_papers.scalars().all())
            
            failed_papers = await db.execute(
                select(Paper).where(
                    and_(
                        Paper.file_path.isnot(None),
                        Paper.processing_error.isnot(None),
                        Paper.processing_error != ""
                    )
                )
            )
            failed = len(failed_papers.scalars().all())
            
            return {
                "running": self._running,
                "total_papers": total,
                "processed": processed,
                "failed": failed,
                "pending": total - processed,
                "progress_percentage": (processed / total * 100) if total > 0 else 0
            }


# Global instance
background_processor = BackgroundProcessor()