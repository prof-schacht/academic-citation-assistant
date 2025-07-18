"""Verify database state and Zotero sync functionality."""
import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.models import User, ZoteroConfig, ZoteroSync, Paper


async def verify_database_state():
    """Comprehensive database state verification."""
    engine = create_async_engine(settings.database_url, echo=False)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with SessionLocal() as session:
        print("\n" + "="*60)
        print("DATABASE STATE VERIFICATION")
        print("="*60 + "\n")
        
        # 1. Check users
        result = await session.execute(select(User))
        users = result.scalars().all()
        print(f"Total users: {len(users)}")
        for user in users:
            print(f"\nUser: {user.email} (ID: {user.id})")
            
            # Check Zotero config
            result = await session.execute(
                select(ZoteroConfig).where(ZoteroConfig.user_id == user.id)
            )
            config = result.scalar_one_or_none()
            
            if config:
                print("  ✓ Has Zotero configuration")
                print(f"    - Zotero User ID: {config.zotero_user_id}")
                print(f"    - Last sync: {config.last_sync}")
                print(f"    - Last sync status: {config.last_sync_status}")
                
                # Parse collections
                if config.selected_collections:
                    try:
                        collections = json.loads(config.selected_collections)
                        print(f"    - Selected collections: {collections}")
                    except:
                        print(f"    - Selected collections (raw): {config.selected_collections}")
                        
                # Parse groups
                if config.selected_groups:
                    try:
                        groups = json.loads(config.selected_groups)
                        print(f"    - Selected groups: {groups}")
                    except:
                        print(f"    - Selected groups (raw): {config.selected_groups}")
            else:
                print("  ✗ No Zotero configuration")
                
            # Check synced papers
            result = await session.execute(
                select(ZoteroSync).where(ZoteroSync.user_id == user.id)
            )
            syncs = result.scalars().all()
            print(f"  - Synced papers: {len(syncs)}")
            
        # 2. Check total papers
        result = await session.execute(select(Paper))
        papers = result.scalars().all()
        print(f"\n\nTotal papers in database: {len(papers)}")
        
        # Show recent papers
        if papers:
            print("\nMost recent papers:")
            sorted_papers = sorted(papers, key=lambda p: p.created_at, reverse=True)
            for paper in sorted_papers[:5]:
                print(f"  - {paper.title[:60]}...")
                print(f"    Created: {paper.created_at}")
                print(f"    Source: {paper.source}")
                if paper.zotero_key:
                    print(f"    Zotero key: {paper.zotero_key}")
                    
        # 3. Check for orphaned papers
        result = await session.execute(
            text("""
                SELECT COUNT(*) FROM papers p
                WHERE NOT EXISTS (
                    SELECT 1 FROM zotero_sync z
                    WHERE z.paper_id = p.id
                )
            """)
        )
        orphaned_count = result.scalar()
        print(f"\nOrphaned papers (not linked to any user): {orphaned_count}")
        
        # 4. Check for duplicate papers
        result = await session.execute(
            text("""
                SELECT title, COUNT(*) as count
                FROM papers
                GROUP BY title
                HAVING COUNT(*) > 1
                ORDER BY count DESC
                LIMIT 5
            """)
        )
        duplicates = result.fetchall()
        if duplicates:
            print("\nDuplicate papers found:")
            for title, count in duplicates:
                print(f"  - '{title[:50]}...': {count} copies")
        else:
            print("\nNo duplicate papers found")
            
        # 5. Check processing status
        result = await session.execute(
            text("""
                SELECT 
                    is_processed,
                    COUNT(*) as count,
                    COUNT(CASE WHEN processing_error IS NOT NULL THEN 1 END) as error_count
                FROM papers
                GROUP BY is_processed
            """)
        )
        processing_stats = result.fetchall()
        print("\nPaper processing status:")
        for is_processed, count, error_count in processing_stats:
            status = "Processed" if is_processed else "Not processed"
            print(f"  - {status}: {count} papers ({error_count} with errors)")
            
    await engine.dispose()


async def test_zotero_api_directly():
    """Test Zotero API directly to verify connectivity."""
    import aiohttp
    
    engine = create_async_engine(settings.database_url, echo=False)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with SessionLocal() as session:
        # Get test user's Zotero config
        result = await session.execute(
            select(ZoteroConfig).join(User).where(User.email == "test@example.com")
        )
        config = result.scalar_one_or_none()
        
        if not config:
            print("No Zotero configuration found for test user")
            return
            
        print("\n" + "="*60)
        print("DIRECT ZOTERO API TEST")
        print("="*60 + "\n")
        
        headers = {
            "Zotero-API-Key": config.api_key,
            "Zotero-API-Version": "3"
        }
        
        async with aiohttp.ClientSession(headers=headers) as http_session:
            # Test 1: Get user info
            url = f"https://api.zotero.org/users/{config.zotero_user_id}"
            async with http_session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✓ User info retrieved: {data.get('username', 'N/A')}")
                else:
                    print(f"✗ Failed to get user info: {response.status}")
                    
            # Test 2: Count items in personal library
            url = f"https://api.zotero.org/users/{config.zotero_user_id}/items?format=json&limit=1"
            async with http_session.get(url) as response:
                if response.status == 200:
                    total = response.headers.get('Total-Results', '0')
                    print(f"✓ Personal library has {total} total items")
                else:
                    print(f"✗ Failed to get library items: {response.status}")
                    
            # Test 3: Get items from selected collections
            if config.selected_collections:
                collections = json.loads(config.selected_collections)
                for collection_key in collections[:3]:  # Test first 3
                    url = f"https://api.zotero.org/users/{config.zotero_user_id}/collections/{collection_key}/items?format=json&limit=5"
                    async with http_session.get(url) as response:
                        if response.status == 200:
                            items = await response.json()
                            print(f"✓ Collection {collection_key}: {len(items)} items retrieved")
                            for item in items[:2]:
                                data = item.get('data', {})
                                title = data.get('title', 'No title')
                                print(f"    - {title[:50]}...")
                        else:
                            print(f"✗ Failed to get items from collection {collection_key}: {response.status}")
                            
    await engine.dispose()


async def main():
    """Run all verification tests."""
    await verify_database_state()
    await test_zotero_api_directly()


if __name__ == "__main__":
    asyncio.run(main())