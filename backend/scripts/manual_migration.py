#!/usr/bin/env python3
"""Manual migration script to add missing columns to paper_chunks table."""
import asyncio
from sqlalchemy import text
from app.db.session import AsyncSessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_migration():
    """Run the migration to add missing columns."""
    async with AsyncSessionLocal() as session:
        try:
            # Add columns if they don't exist
            await session.execute(text("""
                ALTER TABLE paper_chunks 
                ADD COLUMN IF NOT EXISTS chunk_type VARCHAR(50),
                ADD COLUMN IF NOT EXISTS sentence_count INTEGER,
                ADD COLUMN IF NOT EXISTS semantic_score FLOAT,
                ADD COLUMN IF NOT EXISTS chunk_metadata JSON
            """))
            
            await session.commit()
            logger.info("Migration completed successfully!")
            
            # Verify columns were added
            result = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'paper_chunks' 
                AND column_name IN ('chunk_type', 'sentence_count', 'semantic_score', 'chunk_metadata')
            """))
            
            columns = [row[0] for row in result]
            logger.info(f"Verified columns exist: {columns}")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(run_migration())