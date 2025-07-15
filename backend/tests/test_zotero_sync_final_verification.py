#!/usr/bin/env python3
"""
Final verification test for Zotero sync functionality.
Tests all critical aspects:
1. Sync process with collection configuration
2. Papers are actually imported (not 0)
3. Progress bar shows meaningful progress
4. PDFs are properly attached and processed
"""

import asyncio
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from app.models import User, ZoteroConfig, Paper, ZoteroSync
from app.services.zotero_service import ZoteroService
from app.core.config import settings
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
TEST_USER_EMAIL = "test@example.com"
TEST_ZOTERO_API_KEY = os.getenv("ZOTERO_API_KEY", "YOUR_API_KEY")
TEST_ZOTERO_USER_ID = os.getenv("ZOTERO_USER_ID", "YOUR_USER_ID")
TEST_COLLECTION_KEY = "CPUVP4AQ"  # Your specific collection


async def run_final_verification():
    """Run comprehensive Zotero sync verification."""
    # Create database engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_maker() as session:
        # 1. Get or create test user
        result = await session.execute(
            select(User).where(User.email == TEST_USER_EMAIL)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            logger.info(f"Creating test user: {TEST_USER_EMAIL}")
            user = User(email=TEST_USER_EMAIL, name="Test User")
            session.add(user)
            await session.commit()
        
        # 2. Configure Zotero with collection
        logger.info("\n=== Configuring Zotero Integration ===")
        result = await session.execute(
            select(ZoteroConfig).where(ZoteroConfig.user_id == user.id)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            config = ZoteroConfig(
                user_id=user.id,
                api_key=TEST_ZOTERO_API_KEY,
                zotero_user_id=TEST_ZOTERO_USER_ID
            )
            session.add(config)
        else:
            config.api_key = TEST_ZOTERO_API_KEY
            config.zotero_user_id = TEST_ZOTERO_USER_ID
        
        # Set the collection with proper format
        config.selected_collections = json.dumps([{
            "key": TEST_COLLECTION_KEY,
            "libraryId": f"users/{TEST_ZOTERO_USER_ID}"
        }])
        
        await session.commit()
        logger.info(f"Configured collection: {TEST_COLLECTION_KEY}")
        
        # 3. Count papers before sync
        result = await session.execute(
            select(func.count()).select_from(Paper)
            .join(ZoteroSync)
            .where(ZoteroSync.user_id == user.id)
        )
        papers_before = result.scalar() or 0
        logger.info(f"Papers before sync: {papers_before}")
        
        # 4. Run sync with progress tracking
        logger.info("\n=== Starting Zotero Sync ===")
        async with ZoteroService(session, user.id) as service:
            # Track progress updates
            progress_updates = []
            
            # Create a task to monitor progress
            async def monitor_progress():
                last_message = ""
                while True:
                    progress = service.get_sync_progress()
                    if progress['message'] != last_message:
                        last_message = progress['message']
                        progress_updates.append(progress.copy())
                        logger.info(f"Progress: {progress['status']} - {progress['message']}")
                        if progress['total'] > 0:
                            percentage = (progress['current'] / progress['total']) * 100
                            logger.info(f"  [{progress['current']}/{progress['total']}] {percentage:.1f}%")
                    
                    if progress['status'] == 'completed':
                        break
                    
                    await asyncio.sleep(0.5)
            
            # Start monitoring
            monitor_task = asyncio.create_task(monitor_progress())
            
            # Run sync
            try:
                new_papers, updated_papers, failed_papers = await service.sync_library(force_full_sync=True)
                
                # Wait for monitoring to complete
                await monitor_task
                
                logger.info(f"\nSync Results:")
                logger.info(f"  New papers: {new_papers}")
                logger.info(f"  Updated papers: {updated_papers}")
                logger.info(f"  Failed papers: {failed_papers}")
                
                # Verify sync actually imported papers
                if new_papers + updated_papers == 0:
                    logger.error("❌ FAILED: No papers were synced!")
                else:
                    logger.info(f"✅ SUCCESS: {new_papers + updated_papers} papers synced")
                
            except Exception as e:
                logger.error(f"Sync failed: {e}", exc_info=True)
                monitor_task.cancel()
                return
        
        # 5. Verify papers were imported
        logger.info("\n=== Verifying Import Results ===")
        
        # Count papers after sync
        result = await session.execute(
            select(func.count()).select_from(Paper)
            .join(ZoteroSync)
            .where(ZoteroSync.user_id == user.id)
        )
        papers_after = result.scalar() or 0
        
        papers_imported = papers_after - papers_before
        logger.info(f"Papers after sync: {papers_after}")
        logger.info(f"Papers imported in this sync: {papers_imported}")
        
        # Get details of imported papers
        result = await session.execute(
            select(Paper)
            .join(ZoteroSync)
            .where(ZoteroSync.user_id == user.id)
            .order_by(Paper.created_at.desc())
            .limit(10)
        )
        recent_papers = result.scalars().all()
        
        if recent_papers:
            logger.info("\nRecent papers:")
            for i, paper in enumerate(recent_papers, 1):
                logger.info(f"  {i}. {paper.title[:80]}...")
                logger.info(f"     - Authors: {', '.join(paper.authors[:3]) if paper.authors else 'No authors'}")
                logger.info(f"     - Year: {paper.year}")
                logger.info(f"     - Has PDF: {'Yes' if paper.file_path else 'No'}")
                logger.info(f"     - Processed: {'Yes' if paper.is_processed else 'No'}")
        
        # 6. Verify PDF processing
        logger.info("\n=== PDF Processing Status ===")
        
        # Count PDFs
        result = await session.execute(
            select(func.count()).select_from(Paper)
            .join(ZoteroSync)
            .where(
                ZoteroSync.user_id == user.id,
                Paper.file_path.isnot(None)
            )
        )
        papers_with_pdfs = result.scalar() or 0
        
        # Count processed papers
        result = await session.execute(
            select(func.count()).select_from(Paper)
            .join(ZoteroSync)
            .where(
                ZoteroSync.user_id == user.id,
                Paper.is_processed == True
            )
        )
        papers_processed = result.scalar() or 0
        
        logger.info(f"Papers with PDFs: {papers_with_pdfs}")
        logger.info(f"Papers processed: {papers_processed}")
        
        # 7. Verify progress tracking
        logger.info("\n=== Progress Tracking Verification ===")
        if progress_updates:
            logger.info(f"Progress updates received: {len(progress_updates)}")
            
            # Check if progress showed meaningful updates
            max_total = max(p.get('total', 0) for p in progress_updates)
            max_current = max(p.get('current', 0) for p in progress_updates)
            
            if max_total > 0 and max_current > 0:
                logger.info(f"✅ Progress tracking working: showed {max_current}/{max_total} items")
            else:
                logger.warning("⚠️  Progress tracking may not be working correctly")
        else:
            logger.warning("⚠️  No progress updates received")
        
        # 8. Final verdict
        logger.info("\n=== FINAL VERIFICATION RESULTS ===")
        
        issues = []
        if papers_imported == 0:
            issues.append("No papers were imported")
        if papers_with_pdfs == 0:
            issues.append("No PDFs were downloaded")
        if not progress_updates or max_total == 0:
            issues.append("Progress tracking not working")
        
        if issues:
            logger.error(f"❌ VERIFICATION FAILED:")
            for issue in issues:
                logger.error(f"   - {issue}")
        else:
            logger.info(f"✅ ALL CHECKS PASSED!")
            logger.info(f"   - {papers_imported} papers imported")
            logger.info(f"   - {papers_with_pdfs} PDFs downloaded")
            logger.info(f"   - Progress tracking working correctly")
            logger.info(f"   - Sync is fully functional!")


if __name__ == "__main__":
    # Check for API credentials
    if TEST_ZOTERO_API_KEY == "YOUR_API_KEY":
        print("Please set ZOTERO_API_KEY environment variable")
        sys.exit(1)
    if TEST_ZOTERO_USER_ID == "YOUR_USER_ID":
        print("Please set ZOTERO_USER_ID environment variable")
        sys.exit(1)
    
    asyncio.run(run_final_verification())