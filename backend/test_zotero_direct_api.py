#!/usr/bin/env python3
"""Test Zotero API directly to verify credentials and group access."""
import httpx
import asyncio
import os

# Get credentials from database config
API_KEY = os.environ.get("ZOTERO_API_KEY", "")
USER_ID = "5008235"
GROUP_ID = "4965330"  # COAI group

async def test_api():
    """Test Zotero API directly."""
    headers = {
        "Zotero-API-Version": "3",
        "Authorization": f"Bearer {API_KEY}" if API_KEY else None
    }
    
    async with httpx.AsyncClient() as client:
        # Test 1: User library
        print(f"Testing user library (users/{USER_ID})...")
        try:
            response = await client.get(
                f"https://api.zotero.org/users/{USER_ID}/items?limit=5",
                headers=headers
            )
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                print(f"  Total items: {response.headers.get('Total-Results', 'Unknown')}")
                items = response.json()
                print(f"  Retrieved {len(items)} items")
            else:
                print(f"  Error: {response.text[:200]}")
        except Exception as e:
            print(f"  Exception: {e}")
        
        # Test 2: Group library
        print(f"\nTesting group library (groups/{GROUP_ID})...")
        try:
            response = await client.get(
                f"https://api.zotero.org/groups/{GROUP_ID}/items?limit=5",
                headers=headers
            )
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                print(f"  Total items: {response.headers.get('Total-Results', 'Unknown')}")
                items = response.json()
                print(f"  Retrieved {len(items)} items")
                if items:
                    print("\n  First item:")
                    item = items[0]
                    data = item.get('data', {})
                    print(f"    Title: {data.get('title', 'N/A')}")
                    print(f"    Type: {data.get('itemType', 'N/A')}")
                    print(f"    Key: {item.get('key', 'N/A')}")
            else:
                print(f"  Error: {response.text[:200]}")
        except Exception as e:
            print(f"  Exception: {e}")
        
        # Test 3: Get API key from database
        if not API_KEY:
            print("\nNo API key in environment. Fetching from database...")
            import sys
            from pathlib import Path
            backend_path = Path(__file__).parent
            sys.path.insert(0, str(backend_path))
            
            from uuid import UUID
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy import select
            from app.models import ZoteroConfig
            
            engine = create_async_engine("postgresql+asyncpg://citation_user:citation_pass@localhost:5432/citation_db")
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            async with async_session() as db:
                result = await db.execute(
                    select(ZoteroConfig).where(ZoteroConfig.user_id == UUID("00000000-0000-0000-0000-000000000001"))
                )
                config = result.scalar_one_or_none()
                if config:
                    print(f"  Found API key in database")
                    # Rerun test with API key
                    headers["Authorization"] = f"Bearer {config.api_key}"
                    
                    print(f"\nRetrying group library with API key from database...")
                    response = await client.get(
                        f"https://api.zotero.org/groups/{GROUP_ID}/items?limit=5",
                        headers=headers
                    )
                    print(f"  Status: {response.status_code}")
                    if response.status_code == 200:
                        print(f"  Total items: {response.headers.get('Total-Results', 'Unknown')}")
                    else:
                        print(f"  Error: {response.text[:200]}")
            
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_api())