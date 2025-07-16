#!/usr/bin/env python3
"""Debug Zotero sync to see what's happening."""
import asyncio
import os
import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

os.environ["DATABASE_URL"] = "postgresql+asyncpg://citation_user:citation_pass@localhost:5432/citation_db"

from uuid import UUID
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.zotero_service import ZoteroService
from app.services.logging_service import LoggingService
from app.models.system_log import LogLevel, LogCategory

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

async def debug_sync():
    """Debug the Zotero sync process."""
    # Create database session
    engine = create_async_engine(os.environ["DATABASE_URL"])
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        print("Starting Zotero sync debug...")
        
        try:
            # Create service
            service = ZoteroService(db, TEST_USER_ID)
            
            # Check configuration
            await service._load_config()
            config = service._config
            if not config:
                print("ERROR: No Zotero configuration found!")
                return
                
            print(f"Configuration found:")
            print(f"  API Key: {'*' * 10}")
            print(f"  User ID: {config.zotero_user_id}")
            print(f"  Selected Groups: {config.selected_groups}")
            print(f"  Selected Collections: {config.selected_collections}")
            
            # Test API connection
            print("\nTesting API connection...")
            try:
                connection_ok = await service.test_connection()
                print(f"  Connection: {'OK' if connection_ok else 'FAILED'}")
            except Exception as e:
                print(f"  Connection test error: {e}")
                connection_ok = False
            
            if not connection_ok:
                print("Cannot proceed without valid connection")
                # Try anyway to see what happens
                # return
            
            # Fetch library items
            print("\nFetching library items...")
            import json
            selected_groups = json.loads(config.selected_groups) if config.selected_groups else []
            selected_collections = json.loads(config.selected_collections) if config.selected_collections else []
            print(f"  Parsed groups: {selected_groups}")
            print(f"  Parsed collections: {selected_collections}")
            
            papers, attachments = await service.fetch_library_items()
            print(f"  Found {len(papers)} papers")
            print(f"  Found {sum(len(atts) for atts in attachments.values())} attachments")
            
            # Show first few papers
            if papers:
                print("\nFirst 3 papers:")
                for i, paper in enumerate(papers[:3]):
                    data = paper.get('data', {})
                    print(f"  {i+1}. {data.get('title', 'No title')}")
                    print(f"     Key: {paper.get('key')}")
                    print(f"     Type: {data.get('itemType')}")
                    print(f"     Collections: {data.get('collections', [])}")
            
            # Try a full sync
            print("\n\nRunning full sync...")
            new_papers, updated_papers, failed_papers = await service.sync_library(force_full_sync=True)
            print(f"Sync results: {new_papers} new, {updated_papers} updated, {failed_papers} failed")
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(debug_sync())