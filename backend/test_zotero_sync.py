#!/usr/bin/env python3
"""Test Zotero sync with debug logging."""
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.zotero_service import ZoteroService
import json

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_sync():
    """Test Zotero sync with debug output."""
    # Database connection
    engine = create_async_engine("postgresql+asyncpg://citation_user:citation_pass@localhost:5432/citation_db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            # Check current config
            from sqlalchemy import text
            result = await db.execute(text("SELECT * FROM zotero_config WHERE user_id = '00000000-0000-0000-0000-000000000001'"))
            config = result.fetchone()
            
            if config:
                print(f"Current config:")
                print(f"  API Key: {config.api_key[:10]}...")
                print(f"  Zotero User ID: {config.zotero_user_id}")
                print(f"  Selected Groups: {config.selected_groups}")
                print(f"  Selected Collections: {config.selected_collections}")
                print()
            
            # Create service and check what libraries it will fetch
            service = ZoteroService(db, "00000000-0000-0000-0000-000000000001")
            await service._load_config()
            
            # Check selected groups
            selected_groups = []
            if service._config.selected_groups:
                selected_groups = json.loads(service._config.selected_groups)
                print(f"Will fetch from groups: {selected_groups}")
            
            # Test fetching items
            print("\nTesting fetch_library_items...")
            service._session = aiohttp.ClientSession(
                headers={
                    "Zotero-API-Key": service._config.api_key,
                    "Zotero-API-Version": "3"
                }
            )
            
            try:
                papers, attachments_by_parent = await service.fetch_library_items()
                print(f"Fetched {len(papers)} papers")
                print(f"Fetched {sum(len(atts) for atts in attachments_by_parent.values())} PDF attachments")
                
                if papers:
                    print(f"\nFirst paper: {papers[0].get('data', {}).get('title', 'No title')}")
                    paper_key = papers[0].get('key')
                    if paper_key in attachments_by_parent:
                        print(f"  Has {len(attachments_by_parent[paper_key])} PDF attachment(s)")
                
                # Show summary of papers with PDFs
                papers_with_pdfs = sum(1 for key in attachments_by_parent if attachments_by_parent[key])
                print(f"\nTotal papers with PDF attachments: {papers_with_pdfs}")
            finally:
                await service._session.close()
                
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    import aiohttp
    asyncio.run(test_sync())