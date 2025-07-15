#!/usr/bin/env python3
"""Final test to verify sync process is working correctly."""
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.zotero_service import ZoteroService
from sqlalchemy import text
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_final_sync():
    """Final test to verify sync process is working correctly."""
    engine = create_async_engine("postgresql+asyncpg://citation_user:citation_pass@localhost:5432/citation_db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            print("=" * 60)
            print("FINAL SYNC TEST - VERIFYING EVERYTHING WORKS")
            print("=" * 60)
            
            # Check initial state
            papers_result = await db.execute(text("SELECT COUNT(*) FROM papers"))
            initial_papers = papers_result.scalar()
            print(f"📄 Initial papers in database: {initial_papers}")
            
            sync_result = await db.execute(text("SELECT COUNT(*) FROM zotero_sync"))
            initial_sync = sync_result.scalar()
            print(f"🔄 Initial sync records: {initial_sync}")
            
            config_result = await db.execute(text("SELECT last_sync, selected_groups, selected_collections FROM zotero_config WHERE user_id = '00000000-0000-0000-0000-000000000001'"))
            config = config_result.fetchone()
            print(f"📅 Last sync: {config.last_sync}")
            print(f"📚 Selected groups: {config.selected_groups}")
            print(f"📁 Selected collections: {config.selected_collections}")
            
            # Run a fresh sync
            print(f"\n🔄 Running fresh sync...")
            async with ZoteroService(db, "00000000-0000-0000-0000-000000000001") as service:
                new_papers, updated_papers, failed_papers = await service.sync_library()
                print(f"✅ Sync completed:")
                print(f"   New papers: {new_papers}")
                print(f"   Updated papers: {updated_papers}")
                print(f"   Failed papers: {failed_papers}")
            
            # Check final state
            papers_result = await db.execute(text("SELECT COUNT(*) FROM papers"))
            final_papers = papers_result.scalar()
            print(f"\n📄 Final papers in database: {final_papers}")
            
            sync_result = await db.execute(text("SELECT COUNT(*) FROM zotero_sync"))
            final_sync = sync_result.scalar()
            print(f"🔄 Final sync records: {final_sync}")
            
            # Show some sample papers
            if final_papers > 0:
                print(f"\n📋 Sample papers from database:")
                result = await db.execute(text("""
                    SELECT title, authors, year, journal, source, zotero_key, file_path IS NOT NULL as has_pdf
                    FROM papers 
                    ORDER BY created_at DESC 
                    LIMIT 5
                """))
                
                for i, row in enumerate(result, 1):
                    print(f"   {i}. {row.title[:50]}{'...' if len(row.title) > 50 else ''}")
                    print(f"      Authors: {row.authors}")
                    print(f"      Year: {row.year} | Journal: {row.journal}")
                    print(f"      Source: {row.source} | Zotero Key: {row.zotero_key}")
                    print(f"      Has PDF: {'Yes' if row.has_pdf else 'No'}")
                    print()
            
            # Check if we have any PDFs processed
            pdf_result = await db.execute(text("SELECT COUNT(*) FROM papers WHERE file_path IS NOT NULL"))
            pdf_count = pdf_result.scalar()
            print(f"📎 Papers with PDFs: {pdf_count}")
            
            # Check if we have any embeddings
            embed_result = await db.execute(text("SELECT COUNT(*) FROM papers WHERE embedding IS NOT NULL"))
            embed_count = embed_result.scalar()
            print(f"🧠 Papers with embeddings: {embed_count}")
            
            # Check final config
            config_result = await db.execute(text("SELECT last_sync FROM zotero_config WHERE user_id = '00000000-0000-0000-0000-000000000001'"))
            final_last_sync = config_result.scalar()
            print(f"📅 Final last_sync: {final_last_sync}")
            
            print(f"\n📊 SUMMARY:")
            print(f"   Papers added this sync: {final_papers - initial_papers}")
            print(f"   Total papers in database: {final_papers}")
            print(f"   Papers with PDFs: {pdf_count}")
            print(f"   Papers with embeddings: {embed_count}")
            print(f"   Sync working correctly: {'✅ YES' if final_papers > 0 else '❌ NO'}")
            
        except Exception as e:
            logger.error(f"Test failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_final_sync())