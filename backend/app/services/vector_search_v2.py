"""Simplified vector search service for pgvector - working version."""
import numpy as np
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from app.models.paper import Paper
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
        """Search for similar papers using vector similarity."""
        
        # Validate embedding dimension
        if len(embedding) != self.vector_dim:
            raise ValueError(f"Embedding dimension mismatch: expected {self.vector_dim}, got {len(embedding)}")
            
        try:
            # Use ORM approach with proper vector operations
            # Convert embedding to string format for PostgreSQL
            embedding_str = '[' + ','.join(map(str, embedding.tolist())) + ']'
            
            # Create the similarity expression using raw SQL
            from sqlalchemy import Float
            similarity_expr = (
                1 - func.cast(
                    text(f"embedding <=> '{embedding_str}'::vector"),
                    Float
                )
            ).label('similarity')
            
            # Build query
            query = select(
                Paper,
                similarity_expr
            ).where(
                Paper.is_processed == True,
                similarity_expr > options.min_similarity
            ).order_by(
                similarity_expr.desc()
            ).limit(
                options.limit
            )
            
            # Add filters if provided
            if options.filters:
                if "year_from" in options.filters:
                    query = query.where(Paper.year >= options.filters["year_from"])
                if "year_to" in options.filters:
                    query = query.where(Paper.year <= options.filters["year_to"])
            
            # Execute query
            result = await self.db.execute(query)
            rows = result.all()
            
            # Convert to SearchResult objects
            search_results = []
            for paper, similarity in rows:
                search_results.append(SearchResult(
                    paper_id=str(paper.id),
                    title=paper.title,
                    authors=paper.authors or [],
                    year=paper.year or 0,
                    abstract=paper.abstract or "",
                    similarity=float(similarity),
                    chunk_text=paper.abstract or paper.full_text or "",
                    chunk_index=0,
                    metadata={
                        "journal": paper.journal,
                        "doi": paper.doi,
                        "citation_count": paper.citation_count
                    }
                ))
                
            logger.info(f"Found {len(search_results)} similar papers for user {user_id}")
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