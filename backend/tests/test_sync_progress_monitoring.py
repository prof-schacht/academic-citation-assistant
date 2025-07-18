#!/usr/bin/env python3
"""
Test Zotero sync progress monitoring.
Shows how the progress bar updates during sync.
"""

import asyncio
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models import User, ZoteroConfig
from app.services.zotero_service import ZoteroService
from app.core.config import settings
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_progress_monitoring():
    """Test progress monitoring during Zotero sync."""
    # Create database engine
    engine = create_async_engine(settings.database_url, echo=False)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_maker() as session:
        # Get test user
        result = await session.execute(
            select(User).where(User.email == "test@example.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.error("Test user not found. Please run a sync first.")
            return
        
        # Get Zotero config
        result = await session.execute(
            select(ZoteroConfig).where(ZoteroConfig.user_id == user.id)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            logger.error("Zotero not configured for test user.")
            return
        
        logger.info("=== Testing Zotero Progress Monitoring ===\n")
        logger.info(f"User: {user.email}")
        
        # Parse collections
        collections = []
        if config.selected_collections:
            try:
                collections = json.loads(config.selected_collections)
                logger.info(f"Collections configured: {len(collections)}")
            except:
                pass
        
        # Create service and monitor progress
        async with ZoteroService(session, user.id) as service:
            logger.info("\nTesting progress retrieval...")
            
            # Simulate checking progress during different stages
            stages = [
                ("Initial state", service.get_sync_progress()),
            ]
            
            # Update progress manually to show how it works
            service._update_sync_progress(
                status="fetching",
                current=0,
                total=0,
                message="Connecting to Zotero...",
                libraries_total=1,
                libraries_processed=0
            )
            stages.append(("After start", service.get_sync_progress()))
            
            service._update_sync_progress(
                status="fetching",
                current=0,
                total=0,
                message="Fetching items from Zotero...",
                libraries_total=1,
                libraries_processed=0
            )
            stages.append(("During fetch", service.get_sync_progress()))
            
            service._update_sync_progress(
                status="processing",
                current=10,
                total=50,
                message="Processing 10/50 papers...",
                libraries_total=1,
                libraries_processed=1
            )
            stages.append(("During processing", service.get_sync_progress()))
            
            service._update_sync_progress(
                status="processing",
                current=25,
                total=50,
                message="Processing 25/50 papers (2 new, 3 updated)...",
                libraries_total=1,
                libraries_processed=1
            )
            stages.append(("Midway", service.get_sync_progress()))
            
            service._update_sync_progress(
                status="completed",
                current=50,
                total=50,
                message="Sync complete: 10 new, 15 updated, 0 failed",
                libraries_total=1,
                libraries_processed=1
            )
            stages.append(("Completed", service.get_sync_progress()))
            
            # Display all stages
            logger.info("\n=== Progress States ===")
            for stage_name, progress in stages:
                logger.info(f"\n{stage_name}:")
                logger.info(f"  Status: {progress['status']}")
                logger.info(f"  Progress: {progress['current']}/{progress['total']}")
                if progress['total'] > 0:
                    percentage = (progress['current'] / progress['total']) * 100
                    logger.info(f"  Percentage: {percentage:.1f}%")
                logger.info(f"  Message: {progress['message']}")
                logger.info(f"  Libraries: {progress['libraries_processed']}/{progress['libraries_total']}")
            
            # Test actual sync progress (partial)
            logger.info("\n=== Testing Actual Sync Progress ===")
            logger.info("Fetching items to check real progress updates...")
            
            try:
                # Just fetch items to see progress, don't do full sync
                items, attachments = await service.fetch_library_items()
                logger.info(f"\nFetch complete:")
                logger.info(f"  Found {len(items)} papers")
                logger.info(f"  Found {sum(len(atts) for atts in attachments.values())} PDF attachments")
                
                # Check final progress state
                final_progress = service.get_sync_progress()
                logger.info(f"\nFinal progress state:")
                logger.info(f"  Status: {final_progress['status']}")
                logger.info(f"  Message: {final_progress['message']}")
                
            except Exception as e:
                logger.error(f"Error during fetch: {e}")
        
        logger.info("\n=== Progress Monitoring Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_progress_monitoring())