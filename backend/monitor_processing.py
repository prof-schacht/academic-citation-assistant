#!/usr/bin/env python3
"""Monitor PDF processing progress."""
import asyncio
import time
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

async def monitor_progress():
    """Monitor processing progress."""
    engine = create_async_engine("postgresql+asyncpg://citation_user:citation_pass@localhost:5432/citation_db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    print("📊 Monitoring PDF Processing Progress...")
    print("-" * 50)
    
    while True:
        async with async_session() as db:
            # Get current stats
            result = await db.execute(text("""
                SELECT 
                    COUNT(*) as total_papers,
                    SUM(CASE WHEN file_path IS NOT NULL THEN 1 ELSE 0 END) as with_pdfs,
                    SUM(CASE WHEN is_processed THEN 1 ELSE 0 END) as processed,
                    SUM(CASE WHEN file_path IS NOT NULL AND NOT is_processed THEN 1 ELSE 0 END) as unprocessed
                FROM papers;
            """))
            stats = result.fetchone()
            
            # Get chunk count
            chunk_result = await db.execute(text("SELECT COUNT(*) FROM paper_chunks"))
            chunk_count = chunk_result.scalar()
            
            # Calculate progress
            progress = (stats.processed / stats.with_pdfs * 100) if stats.with_pdfs > 0 else 0
            
            # Clear line and print status
            print(f"\r📄 Papers: {stats.processed}/{stats.with_pdfs} ({progress:.1f}%) | 🧩 Chunks: {chunk_count} | ⏳ Remaining: {stats.unprocessed}", end="", flush=True)
            
            # Check if done
            if stats.unprocessed == 0:
                print("\n\n✅ All PDFs processed!")
                break
                
        await asyncio.sleep(2)  # Update every 2 seconds
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(monitor_progress())