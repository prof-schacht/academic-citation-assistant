#!/usr/bin/env python3
"""Debug Zotero sync process step by step."""
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.zotero_service import ZoteroService
import json
import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_zotero_sync():
    """Debug Zotero sync process step by step."""
    # Database connection
    engine = create_async_engine("postgresql+asyncpg://citation_user:citation_pass@localhost:5432/citation_db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        try:
            print("=" * 60)
            print("STEP 1: DATABASE STATE CHECK")
            print("=" * 60)
            
            # Check current config
            from sqlalchemy import text
            result = await db.execute(text("SELECT * FROM zotero_config WHERE user_id = '00000000-0000-0000-0000-000000000001'"))
            config = result.fetchone()
            
            if not config:
                print("❌ No Zotero configuration found in database")
                return
                
            print(f"✅ Zotero Config found:")
            print(f"  API Key: {config.api_key[:10]}...")
            print(f"  Zotero User ID: {config.zotero_user_id}")
            print(f"  Selected Groups: {config.selected_groups}")
            print(f"  Selected Collections: {config.selected_collections}")
            print(f"  Auto Sync: {config.auto_sync_enabled}")
            print(f"  Last Sync: {config.last_sync}")
            print()
            
            # Parse JSON fields
            selected_groups = []
            selected_collections = []
            if config.selected_groups:
                try:
                    selected_groups = json.loads(config.selected_groups)
                    print(f"✅ Selected groups (parsed): {selected_groups}")
                except Exception as e:
                    print(f"❌ Error parsing selected_groups: {e}")
            
            if config.selected_collections:
                try:
                    selected_collections = json.loads(config.selected_collections)
                    print(f"✅ Selected collections (parsed): {selected_collections}")
                except Exception as e:
                    print(f"❌ Error parsing selected_collections: {e}")
            
            # Check existing papers and sync records
            papers_result = await db.execute(text("SELECT COUNT(*) FROM papers"))
            papers_count = papers_result.scalar()
            print(f"📄 Total papers in database: {papers_count}")
            
            sync_result = await db.execute(text("SELECT COUNT(*) FROM zotero_sync"))
            sync_count = sync_result.scalar()
            print(f"🔄 Total Zotero sync records: {sync_count}")
            
            print("\n" + "=" * 60)
            print("STEP 2: ZOTERO SERVICE INITIALIZATION")
            print("=" * 60)
            
            # Create service and check what libraries it will fetch
            service = ZoteroService(db, "00000000-0000-0000-0000-000000000001")
            await service._load_config()
            
            print(f"✅ Service initialized with user ID: {service._config.zotero_user_id}")
            
            # Initialize HTTP session
            service._session = aiohttp.ClientSession(
                headers={
                    "Zotero-API-Key": service._config.api_key,
                    "Zotero-API-Version": "3"
                }
            )
            
            print("\n" + "=" * 60)
            print("STEP 3: LIBRARY DETERMINATION LOGIC")
            print("=" * 60)
            
            # Manually check what libraries will be fetched (replicating fetch_library_items logic)
            selected_collections_by_library = {}
            libraries_to_fetch = set(selected_groups)
            
            # Add libraries that contain selected collections
            libraries_to_fetch.update(selected_collections_by_library.keys())
            
            # If no groups/collections selected, fetch from user's personal library
            if not libraries_to_fetch and not selected_collections:
                libraries_to_fetch.add(f"users/{service._config.zotero_user_id}")
                print(f"🔍 No groups/collections selected, will fetch from personal library: users/{service._config.zotero_user_id}")
            
            # If we have old-format collections but no libraries, we need to fetch from all libraries
            if selected_collections and not libraries_to_fetch:
                libraries_to_fetch.add(f"users/{service._config.zotero_user_id}")
                print(f"⚠️  Old-format collections detected, will fetch from personal library: users/{service._config.zotero_user_id}")
            
            print(f"📚 Libraries to fetch from: {list(libraries_to_fetch)}")
            
            print("\n" + "=" * 60)
            print("STEP 4: DIRECT API TESTING")
            print("=" * 60)
            
            # Test each library individually
            for library_id in libraries_to_fetch:
                print(f"\n🔍 Testing library: {library_id}")
                
                # Test basic library access
                url = f"https://api.zotero.org/{library_id}/items?limit=5"
                print(f"   URL: {url}")
                
                try:
                    async with service._session.get(url) as response:
                        print(f"   Status: {response.status}")
                        if response.status == 200:
                            items = await response.json()
                            print(f"   Items found: {len(items)}")
                            
                            if items:
                                print(f"   First item type: {items[0].get('data', {}).get('itemType', 'unknown')}")
                                print(f"   First item title: {items[0].get('data', {}).get('title', 'No title')[:50]}...")
                                
                                # Check if it has collections
                                collections = items[0].get('data', {}).get('collections', [])
                                print(f"   First item collections: {collections}")
                        else:
                            error_text = await response.text()
                            print(f"   Error: {error_text}")
                except Exception as e:
                    print(f"   Exception: {e}")
                    
            print("\n" + "=" * 60)
            print("STEP 5: COLLECTION FILTERING TEST")
            print("=" * 60)
            
            if selected_collections:
                for collection_key in selected_collections:
                    print(f"\n🔍 Testing collection: {collection_key}")
                    
                    # Test fetching items from this collection
                    for library_id in libraries_to_fetch:
                        url = f"https://api.zotero.org/{library_id}/collections/{collection_key}/items?limit=5"
                        print(f"   Testing in {library_id}: {url}")
                        
                        try:
                            async with service._session.get(url) as response:
                                print(f"   Status: {response.status}")
                                if response.status == 200:
                                    items = await response.json()
                                    print(f"   Items in collection: {len(items)}")
                                    
                                    if items:
                                        print(f"   First item: {items[0].get('data', {}).get('title', 'No title')[:50]}...")
                                elif response.status == 404:
                                    print(f"   Collection not found in this library")
                                else:
                                    error_text = await response.text()
                                    print(f"   Error: {error_text}")
                        except Exception as e:
                            print(f"   Exception: {e}")
            
            print("\n" + "=" * 60)
            print("STEP 6: FULL SYNC SIMULATION")
            print("=" * 60)
            
            try:
                papers, attachments_by_parent = await service.fetch_library_items()
                print(f"✅ Sync simulation completed:")
                print(f"   Papers fetched: {len(papers)}")
                print(f"   PDF attachments: {sum(len(atts) for atts in attachments_by_parent.values())}")
                
                if papers:
                    print(f"\n📄 First few papers:")
                    for i, paper in enumerate(papers[:3]):
                        title = paper.get('data', {}).get('title', 'No title')
                        item_type = paper.get('data', {}).get('itemType', 'unknown')
                        collections = paper.get('data', {}).get('collections', [])
                        print(f"   {i+1}. {title[:50]}... (type: {item_type}, collections: {collections})")
                else:
                    print("❌ No papers found!")
                    print("\nPossible reasons:")
                    print("   - Collection filtering is too restrictive")
                    print("   - Selected collections are empty")
                    print("   - API permissions issue")
                    print("   - Collection keys are wrong/outdated")
                
            except Exception as e:
                print(f"❌ Sync simulation failed: {e}")
                logger.error("Sync simulation error", exc_info=True)
                
            finally:
                if service._session:
                    await service._session.close()
                    
        except Exception as e:
            logger.error(f"Debug script failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(debug_zotero_sync())