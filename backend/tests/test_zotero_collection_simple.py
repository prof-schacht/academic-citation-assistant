"""Simple test to verify Zotero collection sync works with old format."""
import asyncio
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Reduce noise
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.models import User, ZoteroConfig, ZoteroSync
from app.services.zotero_service import ZoteroService


async def test_sync():
    """Test sync with old format collections."""
    engine = create_async_engine(settings.database_url, echo=False)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with SessionLocal() as session:
        # Get test user
        result = await session.execute(
            select(User).where(User.email == "test@example.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.error("Test user not found")
            return
            
        # Check configuration
        result = await session.execute(
            select(ZoteroConfig).where(ZoteroConfig.user_id == user.id)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            logger.error("No Zotero configuration found")
            return
            
        logger.info("Current configuration:")
        if config.selected_collections:
            collections = json.loads(config.selected_collections)
            logger.info(f"  Collections: {collections}")
            is_old_format = any(isinstance(c, str) for c in collections)
            logger.info(f"  Old format: {is_old_format}")
        else:
            logger.info("  No collections selected")
            
        # Run sync
        async with ZoteroService(session, user.id) as service:
            logger.info("\nStarting sync...")
            try:
                new_papers, updated_papers, failed_papers = await service.sync_library(force_full_sync=True)
                
                logger.info(f"\nSync complete:")
                logger.info(f"  New papers: {new_papers}")
                logger.info(f"  Updated papers: {updated_papers}")
                logger.info(f"  Failed papers: {failed_papers}")
                
                # Count total synced papers
                result = await session.execute(
                    select(ZoteroSync).where(ZoteroSync.user_id == user.id)
                )
                total_synced = len(result.scalars().all())
                logger.info(f"  Total papers synced: {total_synced}")
                
                if new_papers > 0 or updated_papers > 0:
                    logger.info("\n✓ SUCCESS: Papers were synced from selected collections")
                elif total_synced > 0:
                    logger.info("\n✓ SUCCESS: Papers already synced, no new updates")
                else:
                    logger.warning("\n⚠ WARNING: No papers synced - check collection settings")
                    
            except Exception as e:
                logger.error(f"\n✗ ERROR: Sync failed - {e}", exc_info=True)
                
    await engine.dispose()


async def test_migration():
    """Test collection format migration."""
    engine = create_async_engine(settings.database_url, echo=False)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with SessionLocal() as session:
        # Get test user
        result = await session.execute(
            select(User).where(User.email == "test@example.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.error("Test user not found")
            return
            
        async with ZoteroService(session, user.id) as service:
            logger.info("\nTesting collection migration...")
            migrated = await service.migrate_collection_format()
            
            if migrated:
                logger.info("✓ Migration completed")
                
                # Check new format
                await session.refresh(service._config)
                if service._config.selected_collections:
                    collections = json.loads(service._config.selected_collections)
                    logger.info(f"New format: {json.dumps(collections, indent=2)}")
            else:
                logger.info("No migration needed - already in new format")
                
    await engine.dispose()


async def main():
    """Run tests."""
    logger.info("="*60)
    logger.info("ZOTERO COLLECTION SYNC TEST")
    logger.info("="*60)
    
    # Test 1: Sync with current format
    await test_sync()
    
    # Test 2: Migration (optional)
    # await test_migration()
    
    # Test 3: Sync after migration (uncomment if migration was run)
    # logger.info("\n" + "="*60)
    # logger.info("TESTING SYNC AFTER MIGRATION")
    # logger.info("="*60)
    # await test_sync()


if __name__ == "__main__":
    asyncio.run(main())