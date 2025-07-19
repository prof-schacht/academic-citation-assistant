"""Simplified vector search service for pgvector - working version."""
import numpy as np
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from app.models.paper import Paper
from app.models.paper_chunk import PaperChunk
from app.core.config import settings
from dataclasses import dataclass
import logging
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a search result from vector similarity search."""
    paper_id: str
    title: str
    authors: List[str]
    year: int
    abstract: str
    similarity: float
    chunk_text: str
    chunk_index: int
    metadata: Dict[str, Any]


@dataclass
class SearchOptions:
    """Options for vector search."""
    limit: int = 10
    min_similarity: float = 0.5
    filters: Optional[Dict[str, Any]] = None


class VectorSearchService:
    """Simplified vector search service for papers."""
    
    def __init__(self, db: AsyncSession):
        """Initialize the vector search service."""
        self.db = db
        self.vector_dim = settings.embedding_dimension
        
    async def search_similar_chunks(
        self,
        embedding: np.ndarray,
        user_id: str,
        options: SearchOptions = SearchOptions()
    ) -> List[SearchResult]:
        """Search for similar chunks across all papers using vector similarity."""
        
        # Validate embedding dimension
        if len(embedding) != self.vector_dim:
            raise ValueError(f"Embedding dimension mismatch: expected {self.vector_dim}, got {len(embedding)}")
            
        try:
            # Convert embedding to string format for PostgreSQL
            embedding_str = '[' + ','.join(map(str, embedding.tolist())) + ']'
            
            # Create the similarity expression for chunks
            from sqlalchemy import Float
            similarity_expr = (
                1 - func.cast(
                    text(f"pc.embedding <=> '{embedding_str}'::vector"),
                    Float
                )
            ).label('similarity')
            
            # Build query to search chunks, not entire papers
            query = select(
                PaperChunk,
                Paper,
                similarity_expr
            ).join(
                Paper, PaperChunk.paper_id == Paper.id
            ).where(
                and_(
                    Paper.is_processed == True,
                    similarity_expr > options.min_similarity
                )
            ).order_by(
                similarity_expr.desc()
            ).limit(
                options.limit * 2  # Get more chunks, then deduplicate by paper
            )
            
            # Add paper-level filters if provided
            if options.filters:
                if "year_from" in options.filters:
                    query = query.where(Paper.year >= options.filters["year_from"])
                if "year_to" in options.filters:
                    query = query.where(Paper.year <= options.filters["year_to"])
            
            # Execute query with alias for PaperChunk
            query_str = str(query.compile(compile_kwargs={"literal_binds": True}))
            query_str = query_str.replace("paper_chunks.", "pc.")
            
            # Use a raw query for better control
            raw_query = f"""
                SELECT 
                    pc.id as chunk_id,
                    pc.content as chunk_content,
                    pc.chunk_index,
                    pc.section_title,
                    pc.page_start,
                    pc.page_end,
                    pc.page_boundaries,
                    p.id as paper_id,
                    p.title,
                    p.authors,
                    p.year,
                    p.abstract,
                    p.journal,
                    p.doi,
                    p.citation_count,
                    1 - (pc.embedding <=> '{embedding_str}'::vector) as similarity
                FROM paper_chunks pc
                JOIN papers p ON pc.paper_id = p.id
                WHERE p.is_processed = true
                    AND 1 - (pc.embedding <=> '{embedding_str}'::vector) > {options.min_similarity}
                ORDER BY similarity DESC
                LIMIT {options.limit * 2}
            """
            
            result = await self.db.execute(text(raw_query))
            rows = result.fetchall()
            
            # Convert to SearchResult objects and deduplicate by paper
            search_results = []
            seen_papers = set()
            
            for row in rows:
                paper_id = str(row.paper_id)
                
                # For now, include multiple chunks from same paper (better coverage)
                # Later we can deduplicate if needed
                search_results.append(SearchResult(
                    paper_id=paper_id,
                    title=row.title,
                    authors=row.authors or [],
                    year=row.year or 0,
                    abstract=row.abstract or "",
                    similarity=float(row.similarity),
                    chunk_text=row.chunk_content,
                    chunk_index=row.chunk_index,
                    metadata={
                        "journal": row.journal,
                        "doi": row.doi,
                        "citation_count": row.citation_count,
                        "section": row.section_title,
                        "chunk_id": str(row.chunk_id),
                        "page_start": row.page_start,
                        "page_end": row.page_end,
                        "page_boundaries": row.page_boundaries
                    }
                ))
                
                # Limit to requested number of results
                if len(search_results) >= options.limit:
                    break
                
            logger.info(f"Found {len(search_results)} similar chunks for user {user_id}")
            return search_results
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            raise
            
    async def search_multiple_indexes(
        self,
        embedding: np.ndarray,
        indexes: List[str]
    ) -> List[SearchResult]:
        """Search across multiple indexes."""
        # For now, just search the local index
        results = []
        
        for index in indexes:
            if index == "local":
                local_results = await self.search_similar_chunks(
                    embedding,
                    user_id="system",
                    options=SearchOptions(limit=5)
                )
                results.extend(local_results)
                
        # Sort all results by similarity
        results.sort(key=lambda x: x.similarity, reverse=True)
        
        return results