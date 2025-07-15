#!/usr/bin/env python3
"""Test the timestamp filtering issue."""
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

async def test_timestamp_issue():
    """Test the timestamp filtering issue."""
    engine = create_async_engine("postgresql+asyncpg://citation_user:citation_pass@localhost:5432/citation_db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            print("=" * 60)
            print("TESTING TIMESTAMP FILTERING ISSUE")
            print("=" * 60)
            
            # Check the last sync timestamp
            result = await db.execute(text("SELECT last_sync FROM zotero_config WHERE user_id = '00000000-0000-0000-0000-000000000001'"))
            last_sync = result.scalar()
            print(f"📅 Last sync timestamp: {last_sync}")
            
            if last_sync:
                print(f"📅 Timestamp as Unix time: {int(last_sync.timestamp())}")
                
            # Test fetch without timestamp filter
            print(f"\n1. Testing fetch WITHOUT timestamp filter...")
            service = ZoteroService(db, "00000000-0000-0000-0000-000000000001")
            await service._load_config()
            
            import aiohttp
            service._session = aiohttp.ClientSession(
                headers={
                    "Zotero-API-Key": service._config.api_key,
                    "Zotero-API-Version": "3"
                }
            )
            
            try:
                papers1, attachments1 = await service.fetch_library_items(modified_since=None)
                print(f"✅ Without filter: {len(papers1)} papers, {sum(len(atts) for atts in attachments1.values())} attachments")
                
                # Test fetch WITH timestamp filter
                print(f"\n2. Testing fetch WITH timestamp filter (last_sync)...")
                papers2, attachments2 = await service.fetch_library_items(modified_since=last_sync)
                print(f"✅ With filter: {len(papers2)} papers, {sum(len(atts) for atts in attachments2.values())} attachments")
                
                # Test with a very old timestamp to see if items have been modified
                print(f"\n3. Testing fetch with old timestamp (1 day ago)...")
                from datetime import timedelta
                old_timestamp = datetime.now() - timedelta(days=1)
                papers3, attachments3 = await service.fetch_library_items(modified_since=old_timestamp)
                print(f"✅ With old filter: {len(papers3)} papers, {sum(len(atts) for atts in attachments3.values())} attachments")
                
                # Test direct API call to see what Zotero returns
                print(f"\n4. Testing direct API call with timestamp...")
                url = f"https://api.zotero.org/users/{service._config.zotero_user_id}/items?limit=5"
                if last_sync:
                    url += f"&since={int(last_sync.timestamp())}"
                
                print(f"API URL: {url}")
                async with service._session.get(url) as response:
                    print(f"Status: {response.status}")
                    if response.status == 200:
                        items = await response.json()
                        print(f"Items returned: {len(items)}")
                        if items:
                            print(f"First item: {items[0].get('data', {}).get('title', 'No title')}")
                    else:
                        print(f"Error: {await response.text()}")
                
            finally:
                await service._session.close()
            
            print(f"\n5. Solution: Clear last_sync to force full sync...")
            await db.execute(text("UPDATE zotero_config SET last_sync = NULL WHERE user_id = '00000000-0000-0000-0000-000000000001'"))
            await db.commit()
            print("✅ Cleared last_sync timestamp")
            
            print(f"\n6. Testing full sync after clearing timestamp...")
            async with ZoteroService(db, "00000000-0000-0000-0000-000000000001") as sync_service:
                new_papers, updated_papers, failed_papers = await sync_service.sync_library()
                print(f"✅ Full sync after clearing: New: {new_papers}, Updated: {updated_papers}, Failed: {failed_papers}")
                
        except Exception as e:
            logger.error(f"Test failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_timestamp_issue())