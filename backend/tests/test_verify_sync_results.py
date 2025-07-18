#!/usr/bin/env python3
"""
Verify Zotero sync results by checking the database state.
This test doesn't require API credentials - it just checks what's already synced.
"""

import asyncio
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, and_
from app.models import User, ZoteroConfig, Paper, ZoteroSync, PaperChunk
from app.core.config import settings
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def verify_sync_results():
    """Verify the current state of Zotero sync in the database."""
    # Create database engine
    engine = create_async_engine(settings.database_url, echo=False)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_maker() as session:
        logger.info("=== ZOTERO SYNC VERIFICATION ===\n")
        
        # 1. Check all users with Zotero config
        result = await session.execute(
            select(User)
            .join(ZoteroConfig)
            .distinct()
        )
        users_with_zotero = result.scalars().all()
        
        if not users_with_zotero:
            logger.warning("No users have Zotero configured!")
            return
        
        logger.info(f"Found {len(users_with_zotero)} users with Zotero configuration\n")
        
        # Check each user
        for user in users_with_zotero:
            logger.info(f"=== User: {user.email} ===")
            
            # Get Zotero config
            result = await session.execute(
                select(ZoteroConfig).where(ZoteroConfig.user_id == user.id)
            )
            config = result.scalar_one()
            
            # Parse collections
            collections = []
            if config.selected_collections:
                try:
                    collections = json.loads(config.selected_collections)
                    logger.info(f"Selected collections: {len(collections)}")
                    for col in collections:
                        if isinstance(col, dict):
                            logger.info(f"  - Collection: {col.get('key')} in {col.get('libraryId')}")
                        else:
                            logger.info(f"  - Collection: {col}")
                except:
                    logger.warning("Failed to parse collections")
            
            # Check sync status
            if config.last_sync:
                time_since_sync = datetime.utcnow() - config.last_sync
                logger.info(f"Last sync: {config.last_sync} ({time_since_sync.total_seconds() / 3600:.1f} hours ago)")
                if config.last_sync_status:
                    logger.info(f"Last sync status: {config.last_sync_status}")
            else:
                logger.info("Never synced")
            
            # Count synced papers
            result = await session.execute(
                select(func.count()).select_from(Paper)
                .join(ZoteroSync)
                .where(ZoteroSync.user_id == user.id)
            )
            total_papers = result.scalar() or 0
            
            # Count papers with PDFs
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
            
            # Count papers with chunks
            result = await session.execute(
                select(func.count(func.distinct(PaperChunk.paper_id)))
                .select_from(PaperChunk)
                .join(Paper)
                .join(ZoteroSync)
                .where(ZoteroSync.user_id == user.id)
            )
            papers_with_chunks = result.scalar() or 0
            
            logger.info(f"\nPaper Statistics:")
            logger.info(f"  Total papers synced: {total_papers}")
            logger.info(f"  Papers with PDFs: {papers_with_pdfs} ({papers_with_pdfs/total_papers*100:.1f}%)" if total_papers > 0 else "  Papers with PDFs: 0")
            logger.info(f"  Papers processed: {papers_processed} ({papers_processed/total_papers*100:.1f}%)" if total_papers > 0 else "  Papers processed: 0")
            logger.info(f"  Papers with chunks: {papers_with_chunks}")
            
            # Show recent papers
            if total_papers > 0:
                result = await session.execute(
                    select(Paper)
                    .join(ZoteroSync)
                    .where(ZoteroSync.user_id == user.id)
                    .order_by(Paper.created_at.desc())
                    .limit(5)
                )
                recent_papers = result.scalars().all()
                
                logger.info("\nMost recent papers:")
                for i, paper in enumerate(recent_papers, 1):
                    logger.info(f"  {i}. {paper.title[:60]}...")
                    logger.info(f"     Year: {paper.year}, PDF: {'Yes' if paper.file_path else 'No'}, Processed: {'Yes' if paper.is_processed else 'No'}")
            
            # Check for recent sync activity
            result = await session.execute(
                select(func.count()).select_from(Paper)
                .join(ZoteroSync)
                .where(
                    ZoteroSync.user_id == user.id,
                    Paper.created_at > datetime.utcnow() - timedelta(hours=1)
                )
            )
            recent_syncs = result.scalar() or 0
            
            if recent_syncs > 0:
                logger.info(f"\n✅ Recent activity: {recent_syncs} papers synced in the last hour")
            
            # Verification results
            logger.info("\n=== VERIFICATION RESULTS ===")
            if total_papers == 0:
                logger.error("❌ FAILED: No papers have been synced")
                logger.info("   The sync may have failed or no papers match the collection filter")
            elif papers_with_pdfs == 0:
                logger.warning("⚠️  WARNING: Papers synced but no PDFs downloaded")
            elif papers_processed < papers_with_pdfs:
                logger.warning(f"⚠️  WARNING: {papers_with_pdfs - papers_processed} PDFs not yet processed")
            else:
                logger.info(f"✅ SUCCESS: {total_papers} papers synced successfully!")
                logger.info(f"   {papers_with_pdfs} PDFs downloaded and {papers_processed} processed")
            
            logger.info("\n" + "="*50 + "\n")


if __name__ == "__main__":
    asyncio.run(verify_sync_results())