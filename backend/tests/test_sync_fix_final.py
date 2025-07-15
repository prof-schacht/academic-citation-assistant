"""Final test to verify Zotero sync fix works correctly."""
import asyncio
import json
import aiohttp
from datetime import datetime
from typing import List, Dict, Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, delete

from app.core.config import settings
from app.models import User, ZoteroConfig, ZoteroSync, Paper
from app.services.zotero_service import ZoteroService


async def test_collection_filtering_logic():
    """Test the collection filtering logic in detail."""
    engine = create_async_engine(settings.database_url, echo=False)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with SessionLocal() as session:
        # Get test user
        result = await session.execute(
            select(User).where(User.email == "test@example.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("Test user not found")
            return
            
        # Get Zotero config
        result = await session.execute(
            select(ZoteroConfig).where(ZoteroConfig.user_id == user.id)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            print("No Zotero configuration found")
            return
            
        print("\n" + "="*60)
        print("TESTING COLLECTION FILTERING LOGIC")
        print("="*60 + "\n")
        
        # Parse selected collections
        selected_collections = json.loads(config.selected_collections) if config.selected_collections else []
        print(f"Selected collections: {selected_collections}")
        
        # Test direct API call with collection filter
        headers = {
            "Zotero-API-Key": config.api_key,
            "Zotero-API-Version": "3"
        }
        
        async with aiohttp.ClientSession(headers=headers) as http_session:
            # Test each collection individually
            for collection_key in selected_collections:
                url = f"https://api.zotero.org/users/{config.zotero_user_id}/collections/{collection_key}/items"
                params = {
                    "format": "json",
                    "limit": 100,
                    "itemType": "-attachment || note"
                }
                
                async with http_session.get(url, params=params) as response:
                    if response.status == 200:
                        items = await response.json()
                        print(f"\nCollection {collection_key}:")
                        print(f"  Total items: {len(items)}")
                        
                        # Analyze item types
                        item_types = {}
                        for item in items:
                            item_type = item.get('data', {}).get('itemType', 'unknown')
                            item_types[item_type] = item_types.get(item_type, 0) + 1
                            
                        print(f"  Item types: {item_types}")
                        
                        # Show sample items
                        for item in items[:3]:
                            data = item.get('data', {})
                            print(f"  - {data.get('title', 'No title')[:50]}...")
                            print(f"    Type: {data.get('itemType')}")
                            print(f"    Key: {data.get('key')}")
                    else:
                        print(f"Failed to fetch collection {collection_key}: {response.status}")
                        
        # Now test with ZoteroService
        print("\n" + "="*60)
        print("TESTING WITH ZOTERO SERVICE")
        print("="*60 + "\n")
        
        async with ZoteroService(session, user.id) as service:
            # Test fetching from personal library with collection filter
            library_id = f"users/{config.zotero_user_id}"
            
            papers, attachments = await service._fetch_items_from_library(
                library_id,
                modified_since=None,
                filter_collections=selected_collections
            )
            
            print(f"Fetched from {library_id}:")
            print(f"  Papers: {len(papers)}")
            print(f"  Attachments: {sum(len(a) for a in attachments.values())}")
            
            if papers:
                print("\nSample papers:")
                for paper in papers[:5]:
                    data = paper.get('data', {})
                    print(f"  - {data.get('title', 'No title')[:50]}...")
                    print(f"    Collections: {data.get('collections', [])}")
                    
    await engine.dispose()


async def test_incremental_sync():
    """Test incremental sync functionality."""
    engine = create_async_engine(settings.database_url, echo=False)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with SessionLocal() as session:
        # Get test user
        result = await session.execute(
            select(User).where(User.email == "test@example.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("Test user not found")
            return
            
        print("\n" + "="*60)
        print("TESTING INCREMENTAL SYNC")
        print("="*60 + "\n")
        
        # Run sync
        async with ZoteroService(session, user.id) as service:
            # First, get current state
            result = await session.execute(
                select(ZoteroSync).where(ZoteroSync.user_id == user.id)
            )
            before_count = len(result.scalars().all())
            print(f"Papers before sync: {before_count}")
            
            # Run incremental sync
            new_papers, updated_papers, failed_papers = await service.sync_library(
                force_full_sync=False
            )
            
            print(f"\nSync results:")
            print(f"  New: {new_papers}")
            print(f"  Updated: {updated_papers}")
            print(f"  Failed: {failed_papers}")
            
            # Check after state
            result = await session.execute(
                select(ZoteroSync).where(ZoteroSync.user_id == user.id)
            )
            after_count = len(result.scalars().all())
            print(f"\nPapers after sync: {after_count}")
            print(f"Net change: {after_count - before_count}")
            
    await engine.dispose()


async def test_force_full_sync():
    """Test force full sync functionality."""
    engine = create_async_engine(settings.database_url, echo=False)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with SessionLocal() as session:
        # Get test user
        result = await session.execute(
            select(User).where(User.email == "test@example.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("Test user not found")
            return
            
        print("\n" + "="*60)
        print("TESTING FORCE FULL SYNC")
        print("="*60 + "\n")
        
        # Clear last sync timestamp to simulate full sync
        result = await session.execute(
            select(ZoteroConfig).where(ZoteroConfig.user_id == user.id)
        )
        config = result.scalar_one_or_none()
        
        if config:
            original_last_sync = config.last_sync
            config.last_sync = None
            await session.commit()
            print("Cleared last sync timestamp")
            
        # Run sync
        async with ZoteroService(session, user.id) as service:
            new_papers, updated_papers, failed_papers = await service.sync_library(
                force_full_sync=True
            )
            
            print(f"\nForce full sync results:")
            print(f"  New: {new_papers}")
            print(f"  Updated: {updated_papers}")
            print(f"  Failed: {failed_papers}")
            
            # Restore original timestamp
            if config and original_last_sync:
                config.last_sync = original_last_sync
                await session.commit()
                
    await engine.dispose()


async def main():
    """Run all final tests."""
    print("FINAL ZOTERO SYNC VERIFICATION TESTS")
    print("="*80)
    
    # Test 1: Collection filtering logic
    await test_collection_filtering_logic()
    
    # Test 2: Incremental sync
    await test_incremental_sync()
    
    # Test 3: Force full sync
    await test_force_full_sync()
    
    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())