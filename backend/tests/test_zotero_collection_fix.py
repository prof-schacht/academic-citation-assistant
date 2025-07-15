"""Test the Zotero collection sync fix for old format collections."""
import asyncio
import logging
import json
from typing import Dict, Any

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
from app.models import User, ZoteroConfig, Paper, ZoteroSync
from app.services.zotero_service import ZoteroService


class CollectionFixTester:
    """Test the collection sync fix."""
    
    def __init__(self):
        self.engine = create_async_engine(settings.database_url, echo=False)
        self.SessionLocal = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
    async def test_old_format_sync(self, user_email: str = "test@example.com"):
        """Test syncing with old format collections."""
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
            logger.info("TESTING OLD FORMAT COLLECTION SYNC")
            logger.info(f"{'='*60}\n")
            
            # Check current collection format
            if config.selected_collections:
                try:
                    collections = json.loads(config.selected_collections)
                    logger.info(f"Current collections format: {collections}")
                    
                    # Check if any are in old format
                    has_old_format = any(isinstance(c, str) for c in collections)
                    logger.info(f"Has old format collections: {has_old_format}")
                except Exception as e:
                    logger.error(f"Failed to parse collections: {e}")
                    
            # Run sync with current format
            async with ZoteroService(session, user.id) as service:
                logger.info("\n--- Running sync with current collection format ---")
                try:
                    new_papers, updated_papers, failed_papers = await service.sync_library(force_full_sync=True)
                    logger.info(f"Sync results: {new_papers} new, {updated_papers} updated, {failed_papers} failed")
                    
                    # Count papers
                    result = await session.execute(
                        select(ZoteroSync).where(ZoteroSync.user_id == user.id)
                    )
                    sync_count = len(result.scalars().all())
                    logger.info(f"Total papers synced: {sync_count}")
                    
                except Exception as e:
                    logger.error(f"Sync failed: {e}", exc_info=True)
                    
    async def test_collection_migration(self, user_email: str = "test@example.com"):
        """Test collection format migration."""
        async with self.SessionLocal() as session:
            # Get user
            result = await session.execute(
                select(User).where(User.email == user_email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.error(f"User {user_email} not found")
                return
                
            logger.info(f"\n{'='*60}")
            logger.info("TESTING COLLECTION FORMAT MIGRATION")
            logger.info(f"{'='*60}\n")
            
            async with ZoteroService(session, user.id) as service:
                # Check if migration is needed
                migrated = await service.migrate_collection_format()
                
                if migrated:
                    logger.info("Migration completed successfully")
                    
                    # Check new format
                    await session.refresh(service._config)
                    if service._config.selected_collections:
                        try:
                            collections = json.loads(service._config.selected_collections)
                            logger.info(f"New collection format: {collections}")
                        except Exception as e:
                            logger.error(f"Failed to parse migrated collections: {e}")
                else:
                    logger.info("No migration needed - collections already in new format")
                    
    async def test_collection_discovery(self, user_email: str = "test@example.com"):
        """Test collection discovery across libraries."""
        async with self.SessionLocal() as session:
            # Get user
            result = await session.execute(
                select(User).where(User.email == user_email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.error(f"User {user_email} not found")
                return
                
            logger.info(f"\n{'='*60}")
            logger.info("TESTING COLLECTION DISCOVERY")
            logger.info(f"{'='*60}\n")
            
            async with ZoteroService(session, user.id) as service:
                # Test the collection discovery logic
                groups = await service.fetch_groups()
                logger.info(f"Found {len(groups)} libraries")
                
                # Map all collections
                all_collections = {}
                for group in groups:
                    lib_id = group['id']
                    logger.info(f"\nLibrary: {lib_id} - {group['name']}")
                    
                    collections = await service.fetch_collections(lib_id)
                    if collections:
                        all_collections[lib_id] = collections
                        for col in collections[:5]:  # Show first 5
                            logger.info(f"  - {col['key']}: {col['name']}")
                        if len(collections) > 5:
                            logger.info(f"  ... and {len(collections) - 5} more")
                            
                # Check selected collections
                result = await session.execute(
                    select(ZoteroConfig).where(ZoteroConfig.user_id == user.id)
                )
                config = result.scalar_one_or_none()
                
                if config and config.selected_collections:
                    logger.info(f"\n--- Checking selected collections ---")
                    try:
                        selected = json.loads(config.selected_collections)
                        for item in selected:
                            if isinstance(item, str):
                                # Old format - find in libraries
                                found_in = []
                                for lib_id, cols in all_collections.items():
                                    for col in cols:
                                        if col['key'] == item:
                                            found_in.append((lib_id, col['name']))
                                            
                                if found_in:
                                    logger.info(f"Collection {item} found in:")
                                    for lib, name in found_in:
                                        logger.info(f"  - {lib}: {name}")
                                else:
                                    logger.warning(f"Collection {item} NOT FOUND in any library")
                            elif isinstance(item, dict):
                                key = item.get('key')
                                lib_id = item.get('libraryId')
                                logger.info(f"Collection {key} assigned to library {lib_id}")
                                
                    except Exception as e:
                        logger.error(f"Failed to parse collections: {e}")
                        
    async def cleanup(self):
        """Clean up resources."""
        await self.engine.dispose()


async def main():
    """Run collection fix tests."""
    tester = CollectionFixTester()
    
    try:
        # Test 1: Collection discovery
        await tester.test_collection_discovery()
        
        # Test 2: Test sync with current format
        await tester.test_old_format_sync()
        
        # Test 3: Test migration
        await tester.test_collection_migration()
        
        # Test 4: Test sync after migration
        logger.info(f"\n{'='*80}")
        logger.info("TESTING SYNC AFTER MIGRATION")
        logger.info(f"{'='*80}\n")
        await tester.test_old_format_sync()
        
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())