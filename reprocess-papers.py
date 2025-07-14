#!/usr/bin/env python3
"""Reprocess uploaded papers to extract better metadata."""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/backend')

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models import Paper
from app.services.paper_processor import PaperProcessorService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reprocess_papers():
    """Reprocess all uploaded papers to extract better metadata."""
    async with AsyncSessionLocal() as db:
        # Get all uploaded papers
        result = await db.execute(
            select(Paper).where(Paper.source == "upload")
        )
        papers = result.scalars().all()
        
        logger.info(f"Found {len(papers)} uploaded papers to reprocess")
        
        for paper in papers:
            logger.info(f"\nReprocessing paper: {paper.title}")
            
            # Find the file path - try multiple locations
            possible_paths = [
                f"backend/uploads/{paper.id}.pdf",
                f"uploads/{paper.id}.pdf",
                f"./{paper.title}",  # Original filename in root
                f"{paper.title}"
            ]
            
            file_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    file_path = path
                    break
            
            if not file_path:
                logger.error(f"File not found in any of: {possible_paths}")
                continue
            
            # Process the paper
            await PaperProcessorService.process_paper(str(paper.id), file_path)
            
            # Refresh the paper to see new metadata
            await db.refresh(paper)
            logger.info(f"New title: {paper.title}")
            logger.info(f"Authors: {paper.authors}")
            logger.info(f"Year: {paper.year}")

if __name__ == "__main__":
    asyncio.run(reprocess_papers())