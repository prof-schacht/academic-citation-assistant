#!/usr/bin/env python3
"""Process all unprocessed PDFs to create chunks and embeddings."""
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_
from app.models import Paper, PaperChunk
from app.services.paper_processor import PaperProcessorService
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def process_unprocessed_papers():
    """Process all papers that have PDFs but aren't processed yet."""
    # Database connection
    engine = create_async_engine("postgresql+asyncpg://citation_user:citation_pass@localhost:5432/citation_db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            # Find unprocessed papers with PDFs
            result = await db.execute(
                select(Paper).where(
                    and_(
                        Paper.file_path.isnot(None),
                        Paper.is_processed == False
                    )
                )
            )
            unprocessed_papers = result.scalars().all()
            
            logger.info(f"Found {len(unprocessed_papers)} unprocessed papers with PDFs")
            
            if not unprocessed_papers:
                logger.info("No papers to process!")
                return
            
            # Process each paper
            success_count = 0
            error_count = 0
            
            for i, paper in enumerate(unprocessed_papers, 1):
                logger.info(f"\nProcessing paper {i}/{len(unprocessed_papers)}: {paper.title[:60]}...")
                
                try:
                    # Check if file exists
                    if not os.path.exists(paper.file_path):
                        logger.error(f"  ❌ File not found: {paper.file_path}")
                        paper.processing_error = "File not found"
                        error_count += 1
                        continue
                    
                    # Process the paper
                    logger.info(f"  📄 Processing PDF: {os.path.basename(paper.file_path)}")
                    
                    # Use the class method to process paper
                    await PaperProcessorService.process_paper(
                        paper_id=str(paper.id),
                        file_path=paper.file_path
                    )
                    
                    # Check if chunks were created
                    chunk_count = await db.execute(
                        select(PaperChunk).where(PaperChunk.paper_id == paper.id)
                    )
                    chunks_created = len(chunk_count.scalars().all())
                    
                    if chunks_created > 0:
                        logger.info(f"  ✅ Created {chunks_created} chunks")
                        success_count += 1
                    else:
                        logger.warning(f"  ⚠️  No chunks created")
                        error_count += 1
                        
                except Exception as e:
                    logger.error(f"  ❌ Error processing paper: {str(e)}")
                    paper.processing_error = str(e)
                    error_count += 1
                
                # Save progress every 5 papers
                if i % 5 == 0:
                    await db.commit()
                    logger.info(f"  💾 Saved progress ({i}/{len(unprocessed_papers)})")
            
            # Final commit
            await db.commit()
            
            # Summary
            logger.info("\n" + "="*50)
            logger.info("PROCESSING COMPLETE!")
            logger.info(f"✅ Successfully processed: {success_count} papers")
            logger.info(f"❌ Failed to process: {error_count} papers")
            
            # Check chunk statistics
            chunk_result = await db.execute(
                select(PaperChunk).limit(5)
            )
            sample_chunks = chunk_result.scalars().all()
            
            if sample_chunks:
                logger.info(f"\n📊 Chunk Statistics:")
                for chunk in sample_chunks[:3]:
                    logger.info(f"  - Chunk {chunk.chunk_index}: {len(chunk.content)} chars")
                    if chunk.embedding:
                        logger.info(f"    Embedding: {len(chunk.embedding)} dimensions")
            
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
        finally:
            await engine.dispose()

if __name__ == "__main__":
    logger.info("=== STARTING PDF PROCESSING ===")
    asyncio.run(process_unprocessed_papers())