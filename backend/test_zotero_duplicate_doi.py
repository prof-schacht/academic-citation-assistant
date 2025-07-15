"""Test script to verify Zotero sync handles duplicate DOIs correctly."""
import asyncio
import sys
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

# Add the project root to the Python path
sys.path.insert(0, '/Users/sschacht/Documents/Playgrounds/academic-citation-assistant/backend')

from app.db.session import async_session
from app.services.zotero_service import ZoteroService
from app.models import Paper, ZoteroSync
from sqlalchemy import select

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test user ID (replace with your actual test user ID)
TEST_USER_ID = UUID("5c19cb8a-b8de-446f-9dc8-b18f1abe456f")


async def test_duplicate_doi_handling():
    """Test that Zotero sync handles duplicate DOIs correctly."""
    async with async_session() as db:
        try:
            # First, let's check current state
            logger.info("Checking current papers with DOIs...")
            result = await db.execute(
                select(Paper).where(Paper.doi.isnot(None)).limit(10)
            )
            papers = result.scalars().all()
            
            logger.info(f"Found {len(papers)} papers with DOIs")
            for paper in papers:
                logger.info(f"  - {paper.title[:50]}... (DOI: {paper.doi})")
            
            # Check Zotero sync records
            logger.info("\nChecking Zotero sync records...")
            result = await db.execute(
                select(ZoteroSync).where(ZoteroSync.user_id == TEST_USER_ID).limit(10)
            )
            syncs = result.scalars().all()
            logger.info(f"Found {len(syncs)} Zotero sync records for user")
            
            # Now run a sync
            logger.info("\nStarting Zotero sync...")
            async with ZoteroService(db, TEST_USER_ID) as zotero:
                # Test connection first
                if not await zotero.test_connection():
                    logger.error("Failed to connect to Zotero API")
                    return
                
                # Run sync
                new, updated, failed = await zotero.sync_library()
                
                logger.info(f"\nSync results:")
                logger.info(f"  New papers: {new}")
                logger.info(f"  Updated papers: {updated}")
                logger.info(f"  Failed papers: {failed}")
                
            # Check state after sync
            logger.info("\nChecking papers after sync...")
            result = await db.execute(
                select(Paper).where(Paper.source == 'zotero').limit(10)
            )
            zotero_papers = result.scalars().all()
            logger.info(f"Found {len(zotero_papers)} papers from Zotero")
            
            # Check for any duplicate DOIs
            logger.info("\nChecking for duplicate DOIs...")
            result = await db.execute(
                select(Paper.doi, Paper.title).where(Paper.doi.isnot(None)).order_by(Paper.doi)
            )
            all_dois = result.all()
            
            doi_counts = {}
            for doi, title in all_dois:
                if doi not in doi_counts:
                    doi_counts[doi] = []
                doi_counts[doi].append(title)
            
            duplicates = {doi: titles for doi, titles in doi_counts.items() if len(titles) > 1}
            
            if duplicates:
                logger.warning(f"Found {len(duplicates)} duplicate DOIs:")
                for doi, titles in duplicates.items():
                    logger.warning(f"  DOI: {doi}")
                    for title in titles:
                        logger.warning(f"    - {title[:50]}...")
            else:
                logger.info("No duplicate DOIs found!")
                
        except Exception as e:
            logger.error(f"Test failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(test_duplicate_doi_handling())