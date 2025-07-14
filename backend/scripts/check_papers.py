#!/usr/bin/env python
"""Check if papers exist in the database."""
import asyncio
from sqlalchemy import select
from app.db.session import get_db
from app.models import Paper

async def check_papers():
    async for db in get_db():
        # Count total papers
        result = await db.execute(select(Paper))
        papers = result.scalars().all()
        
        print(f"Total papers in database: {len(papers)}")
        
        # Count papers with embeddings
        result = await db.execute(select(Paper).where(Paper.embedding != None))
        papers_with_embeddings = result.scalars().all()
        
        print(f"Papers with embeddings: {len(papers_with_embeddings)}")
        
        # Show first few papers
        if papers:
            print("\nFirst 3 papers:")
            for paper in papers[:3]:
                print(f"- {paper.title} (Year: {paper.year})")
                print(f"  Has embedding: {paper.embedding is not None}")
        else:
            print("\nNo papers found! Run: python scripts/populate_test_papers_v2.py")
        
        break

if __name__ == "__main__":
    asyncio.run(check_papers())