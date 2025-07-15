"""Debug test for Zotero collection sync issues."""
import asyncio
import logging
import json
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Reduce noise from other loggers
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.models import User, ZoteroConfig
from app.services.zotero_service import ZoteroService


class CollectionDebugger:
    """Debug tool for collection sync issues."""
    
    def __init__(self):
        self.engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=False)
        self.SessionLocal = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
    async def analyze_collection_setup(self, user_email: str = "zotero_test@example.com"):
        """Analyze the collection setup and potential issues."""
        async with self.SessionLocal() as session:
            # Get user and config
            result = await session.execute(
                select(User).where(User.email == user_email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.error(f"User {user_email} not found")
                return
                
            result = await session.execute(
                select(ZoteroConfig).where(ZoteroConfig.user_id == user.id)
            )
            config = result.scalar_one_or_none()
            
            if not config:
                logger.error("No Zotero configuration found")
                return
                
            logger.info(f"\n{'='*60}")
            logger.info("COLLECTION CONFIGURATION ANALYSIS")
            logger.info(f"{'='*60}\n")
            
            # Parse selected collections
            selected_collections = []
            collection_by_library = {}
            
            if config.selected_collections:
                try:
                    collections_data = json.loads(config.selected_collections)
                    logger.info(f"Raw selected_collections: {collections_data}")
                    
                    for item in collections_data:
                        if isinstance(item, dict):
                            key = item.get('key')
                            lib_id = item.get('libraryId')
                            selected_collections.append(key)
                            if lib_id not in collection_by_library:
                                collection_by_library[lib_id] = []
                            collection_by_library[lib_id].append(key)
                            logger.info(f"  Collection: {key} in library: {lib_id}")
                        else:
                            selected_collections.append(item)
                            logger.info(f"  Collection (old format): {item}")
                except Exception as e:
                    logger.error(f"Failed to parse collections: {e}")
                    
            # Parse selected groups
            selected_groups = []
            if config.selected_groups:
                try:
                    selected_groups = json.loads(config.selected_groups)
                    logger.info(f"\nSelected groups: {selected_groups}")
                except:
                    pass
                    
            # Now test what libraries will be fetched
            logger.info(f"\n{'='*40}")
            logger.info("LIBRARY DETERMINATION LOGIC")
            logger.info(f"{'='*40}\n")
            
            libraries_to_fetch = set(selected_groups)
            libraries_to_fetch.update(collection_by_library.keys())
            
            if not libraries_to_fetch and not selected_collections:
                libraries_to_fetch.add(f"users/{config.zotero_user_id}")
                logger.info("No groups/collections selected - will use personal library")
                
            logger.info(f"Libraries to fetch from: {list(libraries_to_fetch)}")
            
            # Test fetching from each library
            async with ZoteroService(session, user.id) as service:
                logger.info(f"\n{'='*40}")
                logger.info("TESTING ITEM FETCH FROM EACH LIBRARY")
                logger.info(f"{'='*40}\n")
                
                for library_id in libraries_to_fetch:
                    logger.info(f"\nFetching from library: {library_id}")
                    
                    # Determine collections for this library
                    lib_collections = collection_by_library.get(library_id, selected_collections)
                    logger.info(f"Collections filter: {lib_collections}")
                    
                    # Fetch items
                    papers, attachments = await service._fetch_items_from_library(
                        library_id,
                        modified_since=None,
                        filter_collections=lib_collections if lib_collections else None
                    )
                    
                    logger.info(f"Results: {len(papers)} papers, {sum(len(a) for a in attachments.values())} attachments")
                    
                    # Show sample papers
                    if papers:
                        logger.info("Sample papers:")
                        for paper in papers[:3]:
                            data = paper.get('data', {})
                            title = data.get('title', 'No title')
                            collections = data.get('collections', [])
                            logger.info(f"  - {title[:50]}...")
                            logger.info(f"    Collections: {collections}")
                            
    async def test_collection_matching(self, user_email: str = "zotero_test@example.com"):
        """Test the collection matching logic in detail."""
        async with self.SessionLocal() as session:
            # Get user
            result = await session.execute(
                select(User).where(User.email == user_email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.error(f"User {user_email} not found")
                return
                
            async with ZoteroService(session, user.id) as service:
                # Get all collections from all libraries
                logger.info(f"\n{'='*60}")
                logger.info("ALL AVAILABLE COLLECTIONS")
                logger.info(f"{'='*60}\n")
                
                groups = await service.fetch_groups()
                all_collections = {}
                
                for group in groups:
                    lib_id = group['id']
                    logger.info(f"\nLibrary: {lib_id} - {group['name']}")
                    
                    collections = await service.fetch_collections(lib_id)
                    if collections:
                        all_collections[lib_id] = collections
                        for col in collections:
                            logger.info(f"  - {col['key']}: {col['name']}")
                            
                # Now check which collections are selected
                result = await session.execute(
                    select(ZoteroConfig).where(ZoteroConfig.user_id == user.id)
                )
                config = result.scalar_one_or_none()
                
                if config and config.selected_collections:
                    logger.info(f"\n{'='*40}")
                    logger.info("SELECTED vs AVAILABLE COLLECTIONS")
                    logger.info(f"{'='*40}\n")
                    
                    try:
                        selected = json.loads(config.selected_collections)
                        logger.info(f"Selected collections: {selected}")
                        
                        # Check if selected collections exist
                        for sel_item in selected:
                            if isinstance(sel_item, dict):
                                key = sel_item.get('key')
                                lib_id = sel_item.get('libraryId')
                                
                                # Find in available collections
                                found = False
                                if lib_id in all_collections:
                                    for col in all_collections[lib_id]:
                                        if col['key'] == key:
                                            logger.info(f"✓ Found: {key} in {lib_id} - {col['name']}")
                                            found = True
                                            break
                                            
                                if not found:
                                    logger.warning(f"✗ NOT FOUND: {key} in {lib_id}")
                            else:
                                # Old format - search all libraries
                                logger.info(f"Searching for old format collection: {sel_item}")
                                found_in = []
                                for lib_id, cols in all_collections.items():
                                    for col in cols:
                                        if col['key'] == sel_item:
                                            found_in.append((lib_id, col['name']))
                                            
                                if found_in:
                                    logger.info(f"✓ Found in libraries:")
                                    for lib, name in found_in:
                                        logger.info(f"  - {lib}: {name}")
                                else:
                                    logger.warning(f"✗ NOT FOUND in any library")
                                    
                    except Exception as e:
                        logger.error(f"Failed to parse selected collections: {e}")
                        
    async def cleanup(self):
        """Clean up resources."""
        await self.engine.dispose()


async def main():
    """Run collection debugging tests."""
    debugger = CollectionDebugger()
    
    try:
        # Test 1: Analyze collection configuration
        await debugger.analyze_collection_setup()
        
        # Test 2: Test collection matching
        await debugger.test_collection_matching()
        
    finally:
        await debugger.cleanup()


if __name__ == "__main__":
    asyncio.run(main())