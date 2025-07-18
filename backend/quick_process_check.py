#!/usr/bin/env python3
"""Quick check to see processing requirements."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from app.models import Paper
import os

async def check_processing_status():
    """Check what needs to be processed."""
    engine = create_async_engine("postgresql+asyncpg://citation_user:citation_pass@localhost:5432/citation_db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Get statistics
        stats = await db.execute(text("""
            SELECT 
                COUNT(*) as total_papers,
                SUM(CASE WHEN file_path IS NOT NULL THEN 1 ELSE 0 END) as with_pdfs,
                SUM(CASE WHEN is_processed THEN 1 ELSE 0 END) as processed,
                SUM(CASE WHEN file_path IS NOT NULL AND NOT is_processed THEN 1 ELSE 0 END) as need_processing
            FROM papers;
        """))
        
        result = stats.fetchone()
        
        print("📊 Paper Processing Status:")
        print(f"  Total papers: {result.total_papers}")
        print(f"  With PDFs: {result.with_pdfs}")
        print(f"  Already processed: {result.processed}")
        print(f"  Need processing: {result.need_processing}")
        
        # Check if files exist
        papers_with_files = await db.execute(
            select(Paper).where(Paper.file_path.isnot(None)).limit(5)
        )
        
        print("\n📁 Checking file paths:")
        for paper in papers_with_files.scalars():
            exists = os.path.exists(paper.file_path) if paper.file_path else False
            status = "✅" if exists else "❌"
            print(f"  {status} {paper.file_path}")
        
        # Check for chunks
        chunk_count = await db.execute(text("SELECT COUNT(*) FROM paper_chunks"))
        print(f"\n🧩 Total chunks in database: {chunk_count.scalar()}")
        
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_processing_status())