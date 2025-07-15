#!/usr/bin/env python3
"""Test full Zotero sync including PDF downloads and processing."""
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from app.services.zotero_service import ZoteroService
from app.models import Paper, ZoteroSync
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_full_sync():
    """Test full Zotero sync with PDF processing."""
    # Database connection
    engine = create_async_engine("postgresql+asyncpg://citation_user:citation_pass@localhost:5432/citation_db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            # Check current state
            result = await db.execute(
                select(Paper).join(ZoteroSync).where(
                    ZoteroSync.user_id == "00000000-0000-0000-0000-000000000001"
                )
            )
            existing_papers = result.scalars().all()
            print(f"\nCurrent state:")
            print(f"  Papers synced from Zotero: {len(existing_papers)}")
            
            papers_with_pdfs = sum(1 for p in existing_papers if p.file_path)
            print(f"  Papers with PDFs: {papers_with_pdfs}")
            
            # Show a few examples
            if existing_papers:
                print("\nExample papers:")
                for paper in existing_papers[:3]:
                    print(f"  - {paper.title[:60]}...")
                    print(f"    DOI: {paper.doi}")
                    print(f"    Has PDF: {'Yes' if paper.file_path else 'No'}")
                    if paper.file_path:
                        # Check if chunks exist
                        chunks_result = await db.execute(
                            text("SELECT COUNT(*) FROM paper_chunks WHERE paper_id = :paper_id"),
                            {"paper_id": str(paper.id)}
                        )
                        chunks_count = chunks_result.scalar()
                        print(f"    Chunks: {chunks_count}")
            
            # Perform sync
            print("\n" + "="*50)
            print("Starting Zotero sync...")
            print("="*50 + "\n")
            
            async with ZoteroService(db, "00000000-0000-0000-0000-000000000001") as service:
                new_papers, updated_papers, failed_papers = await service.sync_library()
                
                print(f"\nSync results:")
                print(f"  New papers: {new_papers}")
                print(f"  Updated papers: {updated_papers}")
                print(f"  Failed papers: {failed_papers}")
            
            # Check results after sync
            await db.commit()  # Ensure all changes are committed
            
            result = await db.execute(
                select(Paper).join(ZoteroSync).where(
                    ZoteroSync.user_id == "00000000-0000-0000-0000-000000000001"
                )
            )
            all_papers = result.scalars().all()
            
            papers_with_pdfs_after = sum(1 for p in all_papers if p.file_path)
            print(f"\nAfter sync:")
            print(f"  Total papers: {len(all_papers)}")
            print(f"  Papers with PDFs: {papers_with_pdfs_after}")
            print(f"  New PDFs downloaded: {papers_with_pdfs_after - papers_with_pdfs}")
            
            # Show newly added papers
            if new_papers > 0:
                new_paper_result = await db.execute(
                    select(Paper).join(ZoteroSync)
                    .where(ZoteroSync.user_id == "00000000-0000-0000-0000-000000000001")
                    .order_by(Paper.created_at.desc())
                    .limit(new_papers)
                )
                new_paper_list = new_paper_result.scalars().all()
                
                print("\nNewly added papers:")
                for paper in new_paper_list:
                    print(f"  - {paper.title[:60]}...")
                    print(f"    DOI: {paper.doi}")
                    print(f"    Has PDF: {'Yes' if paper.file_path else 'No'}")
                
        except Exception as e:
            logger.error(f"Error during sync: {e}", exc_info=True)
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(test_full_sync())