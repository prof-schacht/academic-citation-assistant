"""Comprehensive test suite for Zotero sync fixes."""
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import aiohttp
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, delete

# Configure logging for detailed debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import from app
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.models import User, ZoteroConfig, ZoteroSync, Paper
from app.services.zotero_service import ZoteroService
from app.db.session import get_db
from app.db.base import Base


class ZoteroSyncTester:
    """Test harness for Zotero sync functionality."""
    
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or settings.database_url
        self.engine = None
        self.SessionLocal = None
        self.test_user = None
        self.zotero_config = None
        
    async def setup(self):
        """Initialize database connection and test user."""
        self.engine = create_async_engine(self.db_url, echo=False)
        self.SessionLocal = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Get or create test user
        async with self.SessionLocal() as session:
            # Look for existing test user with Zotero configuration
            result = await session.execute(
                select(User).where(User.email == "test@example.com")
            )
            self.test_user = result.scalar_one_or_none()
            
            if not self.test_user:
                logger.error("Test user not found. Please ensure test@example.com exists.")
                raise ValueError("Test user not found")
                
            # Get Zotero config
            result = await session.execute(
                select(ZoteroConfig).where(ZoteroConfig.user_id == self.test_user.id)
            )
            self.zotero_config = result.scalar_one_or_none()
            
            if not self.zotero_config:
                logger.error("No Zotero configuration found. Please configure Zotero first.")
                raise ValueError("Zotero not configured for test user")
                
    async def cleanup(self):
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            
    async def test_sync_with_collections(self, force_full_sync: bool = False):
        """Test sync with selected collections."""
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing sync with collections (force_full_sync={force_full_sync})")
        logger.info(f"{'='*60}\n")
        
        async with self.SessionLocal() as session:
            # Display current configuration
            await self._display_config(session)
            
            # Run sync
            async with ZoteroService(session, self.test_user.id) as service:
                try:
                    new_papers, updated_papers, failed_papers = await service.sync_library(
                        force_full_sync=force_full_sync
                    )
                    
                    logger.info(f"\n{'='*40}")
                    logger.info(f"Sync Results:")
                    logger.info(f"  New papers: {new_papers}")
                    logger.info(f"  Updated papers: {updated_papers}")
                    logger.info(f"  Failed papers: {failed_papers}")
                    logger.info(f"  Total synced: {new_papers + updated_papers}")
                    logger.info(f"{'='*40}\n")
                    
                    # Verify papers in database
                    await self._verify_papers(session)
                    
                    return new_papers, updated_papers, failed_papers
                    
                except Exception as e:
                    logger.error(f"Sync failed: {e}", exc_info=True)
                    raise
                    
    async def test_collection_fetching(self):
        """Test fetching collections from all libraries."""
        logger.info(f"\n{'='*60}")
        logger.info("Testing collection fetching")
        logger.info(f"{'='*60}\n")
        
        async with self.SessionLocal() as session:
            async with ZoteroService(session, self.test_user.id) as service:
                # Fetch groups
                groups = await service.fetch_groups()
                logger.info(f"Found {len(groups)} libraries:")
                for group in groups:
                    logger.info(f"  - {group['id']}: {group['name']} ({group['type']})")
                    
                    # Fetch collections for each library
                    collections = await service.fetch_collections(group['id'])
                    if collections:
                        logger.info(f"    Collections ({len(collections)}):")
                        for col in collections:
                            logger.info(f"      - {col['key']}: {col['name']}")
                    else:
                        logger.info("    No collections")
                        
    async def test_direct_api_call(self):
        """Test direct Zotero API calls to verify connectivity."""
        logger.info(f"\n{'='*60}")
        logger.info("Testing direct Zotero API")
        logger.info(f"{'='*60}\n")
        
        async with self.SessionLocal() as session:
            # Load config
            result = await session.execute(
                select(ZoteroConfig).where(ZoteroConfig.user_id == self.test_user.id)
            )
            config = result.scalar_one_or_none()
            
            if not config:
                logger.error("No Zotero configuration found")
                return
                
            # Test API connection
            headers = {
                "Zotero-API-Key": config.api_key,
                "Zotero-API-Version": "3"
            }
            
            async with aiohttp.ClientSession(headers=headers) as http_session:
                # Test user library
                url = f"https://api.zotero.org/users/{config.zotero_user_id}/items?limit=5"
                async with http_session.get(url) as response:
                    logger.info(f"User library test: {response.status}")
                    if response.status == 200:
                        items = await response.json()
                        logger.info(f"  Found {len(items)} items in personal library")
                        
                # Test groups
                url = f"https://api.zotero.org/users/{config.zotero_user_id}/groups"
                async with http_session.get(url) as response:
                    logger.info(f"Groups test: {response.status}")
                    if response.status == 200:
                        groups = await response.json()
                        logger.info(f"  Found {len(groups)} groups")
                        
    async def _display_config(self, session: AsyncSession):
        """Display current Zotero configuration."""
        result = await session.execute(
            select(ZoteroConfig).where(ZoteroConfig.user_id == self.test_user.id)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            logger.error("No Zotero configuration found")
            return
            
        logger.info("Current Zotero Configuration:")
        logger.info(f"  User ID: {config.zotero_user_id}")
        logger.info(f"  API Key: {'*' * 20} (configured)")
        logger.info(f"  Last sync: {config.last_sync}")
        logger.info(f"  Last sync status: {config.last_sync_status}")
        
        # Parse and display selected groups
        if config.selected_groups:
            try:
                groups = json.loads(config.selected_groups)
                logger.info(f"  Selected groups ({len(groups)}):")
                for group in groups:
                    logger.info(f"    - {group}")
            except:
                logger.error(f"  Failed to parse selected groups: {config.selected_groups}")
                
        # Parse and display selected collections
        if config.selected_collections:
            try:
                collections = json.loads(config.selected_collections)
                logger.info(f"  Selected collections ({len(collections)}):")
                for col in collections:
                    if isinstance(col, dict):
                        logger.info(f"    - {col.get('key')} (library: {col.get('libraryId')})")
                    else:
                        logger.info(f"    - {col}")
            except:
                logger.error(f"  Failed to parse selected collections: {config.selected_collections}")
                
    async def _verify_papers(self, session: AsyncSession):
        """Verify papers in database."""
        # Count total papers
        result = await session.execute(select(Paper))
        all_papers = result.scalars().all()
        logger.info(f"\nTotal papers in database: {len(all_papers)}")
        
        # Count Zotero-synced papers
        result = await session.execute(
            select(ZoteroSync).where(ZoteroSync.user_id == self.test_user.id)
        )
        zotero_syncs = result.scalars().all()
        logger.info(f"Papers synced from Zotero: {len(zotero_syncs)}")
        
        # Show recent papers
        if all_papers:
            logger.info("\nMost recent papers:")
            sorted_papers = sorted(all_papers, key=lambda p: p.created_at, reverse=True)
            for paper in sorted_papers[:5]:
                logger.info(f"  - {paper.title[:60]}... (created: {paper.created_at})")
                
    async def clear_sync_history(self):
        """Clear sync history to test full sync."""
        logger.info("\nClearing sync history...")
        
        async with self.SessionLocal() as session:
            # Clear last sync timestamp
            result = await session.execute(
                select(ZoteroConfig).where(ZoteroConfig.user_id == self.test_user.id)
            )
            config = result.scalar_one_or_none()
            
            if config:
                config.last_sync = None
                config.last_sync_status = None
                await session.commit()
                logger.info("Cleared last sync timestamp")
                
            # Optionally clear sync records (but keep papers)
            # await session.execute(
            #     delete(ZoteroSync).where(ZoteroSync.user_id == self.test_user.id)
            # )
            # await session.commit()
            # logger.info("Cleared Zotero sync records")


async def main():
    """Run comprehensive Zotero sync tests."""
    tester = ZoteroSyncTester()
    
    try:
        await tester.setup()
        
        # Test 1: Direct API connectivity
        await tester.test_direct_api_call()
        
        # Test 2: Collection fetching
        await tester.test_collection_fetching()
        
        # Test 3: Normal sync
        logger.info("\n" + "="*80)
        logger.info("TEST 3: Normal incremental sync")
        logger.info("="*80)
        await tester.test_sync_with_collections(force_full_sync=False)
        
        # Test 4: Force full sync
        logger.info("\n" + "="*80)
        logger.info("TEST 4: Force full sync")
        logger.info("="*80)
        await tester.test_sync_with_collections(force_full_sync=True)
        
        # Test 5: Clear history and sync again
        logger.info("\n" + "="*80)
        logger.info("TEST 5: Clear history and sync")
        logger.info("="*80)
        await tester.clear_sync_history()
        await tester.test_sync_with_collections(force_full_sync=False)
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())