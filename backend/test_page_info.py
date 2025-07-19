#!/usr/bin/env python3
"""Test script to check if papers have page information in the database."""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models import Paper, PaperChunk
from app.core.config import settings

async def check_page_info():
    """Check if any papers have page information in their chunks."""
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get all papers
        result = await session.execute(select(Paper).limit(10))
        papers = result.scalars().all()
        
        print(f"Found {len(papers)} papers")
        print("-" * 80)
        
        for paper in papers:
            print(f"\nPaper: {paper.title[:60]}...")
            print(f"Paper ID: {paper.id}")
            
            # Get chunks for this paper
            chunk_result = await session.execute(
                select(PaperChunk)
                .where(PaperChunk.paper_id == paper.id)
                .limit(5)
            )
            chunks = chunk_result.scalars().all()
            
            if chunks:
                print(f"  Found {len(chunks)} chunks")
                for i, chunk in enumerate(chunks):
                    print(f"  Chunk {i+1}:")
                    print(f"    - Text preview: {chunk.content[:50]}...")
                    print(f"    - Page start: {chunk.page_start}")
                    print(f"    - Page end: {chunk.page_end}")
                    print(f"    - Has page boundaries: {chunk.page_boundaries is not None}")
            else:
                print("  No chunks found")
        
        # Check if ANY chunks have page info
        print("\n" + "=" * 80)
        page_info_result = await session.execute(
            select(PaperChunk)
            .where(PaperChunk.page_start.is_not(None))
            .limit(5)
        )
        chunks_with_pages = page_info_result.scalars().all()
        
        if chunks_with_pages:
            print(f"\nFound {len(chunks_with_pages)} chunks with page information:")
            for chunk in chunks_with_pages:
                paper_result = await session.execute(
                    select(Paper).where(Paper.id == chunk.paper_id)
                )
                paper = paper_result.scalar_one()
                print(f"\nPaper: {paper.title[:60]}...")
                print(f"  Chunk: {chunk.content[:50]}...")
                print(f"  Pages: {chunk.page_start} - {chunk.page_end}")
        else:
            print("\nNO chunks found with page information!")
            print("This means PDFs need to be reprocessed to add page information.")

if __name__ == "__main__":
    asyncio.run(check_page_info())