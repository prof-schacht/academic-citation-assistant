"""Vector search service for finding similar papers using pgvector."""
import numpy as np
from typing import List, Optional, Dict, Any
from sqlalchemy import text, select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
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
    """Service for performing vector similarity searches on papers."""
    
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
        """Search for similar paper chunks using vector similarity."""
        
        # Validate embedding dimension
        if len(embedding) != self.vector_dim:
            raise ValueError(f"Embedding dimension mismatch: expected {self.vector_dim}, got {len(embedding)}")
            
        # Convert numpy array to list for PostgreSQL
        embedding_list = embedding.tolist()
        
        # Build the base query using pgvector's <=> operator for cosine distance
        # Note: pgvector returns distance, so we convert to similarity (1 - distance)
        query_str = """
            SELECT 
                p.id,
                p.title,
                p.authors,
                p.year,
                p.abstract,
                p.full_text,
                p.journal,
                p.doi,
                1 - (p.embedding <=> :embedding::vector) as similarity
            FROM papers p
            WHERE 
                1 - (p.embedding <=> :embedding::vector) > :min_similarity
                AND p.is_processed = true
        """
        
        # Prepare parameters dict
        params = {
            "embedding": embedding_list,
            "min_similarity": options.min_similarity
        }
        
        # Add filters if provided
        filter_conditions = []
        
        if options.filters:
            if "year_from" in options.filters:
                filter_conditions.append("p.year >= :year_from")
                params["year_from"] = options.filters["year_from"]
                
            if "year_to" in options.filters:
                filter_conditions.append("p.year <= :year_to")
                params["year_to"] = options.filters["year_to"]
                
        # Combine filter conditions
        if filter_conditions:
            filter_clause = " AND " + " AND ".join(filter_conditions)
            query_str += filter_clause
            
        # Add ordering and limit
        query_str += """
            ORDER BY similarity DESC
            LIMIT :limit
        """
        params["limit"] = options.limit
        
        query = text(query_str)
        
        try:
            # Execute the query with named parameters
            result = await self.db.execute(query, params)
            rows = result.fetchall()
            
            # Convert to SearchResult objects
            search_results = []
            for row in rows:
                search_results.append(SearchResult(
                    paper_id=str(row.id),
                    title=row.title,
                    authors=row.authors or [],
                    year=row.year or 0,
                    abstract=row.abstract or "",
                    similarity=float(row.similarity),
                    chunk_text=row.abstract or row.full_text or "",  # Use abstract as chunk for now
                    chunk_index=0,
                    metadata={"journal": row.journal, "doi": row.doi} if row.journal or row.doi else {}
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
        """Search across multiple indexes (future enhancement for external sources)."""
        # For now, just search the local index
        # In the future, this could query external APIs like Semantic Scholar
        results = []
        
        for index in indexes:
            if index == "local":
                # Search local database
                local_results = await self.search_similar_chunks(
                    embedding,
                    user_id="system",  # System search
                    options=SearchOptions(limit=5)
                )
                results.extend(local_results)
            elif index == "semantic_scholar":
                # TODO: Implement Semantic Scholar API integration
                pass
            elif index == "pubmed":
                # TODO: Implement PubMed API integration
                pass
            elif index == "arxiv":
                # TODO: Implement arXiv API integration
                pass
                
        # Sort all results by similarity
        results.sort(key=lambda x: x.similarity, reverse=True)
        
        return results
        
    async def get_paper_neighbors(
        self,
        paper_id: str,
        limit: int = 5
    ) -> List[SearchResult]:
        """Find papers similar to a given paper."""
        # First, get the paper's embedding
        query = select(Paper).where(Paper.id == paper_id)
        result = await self.db.execute(query)
        paper = result.scalar_one_or_none()
        
        if not paper or not paper.embedding:
            return []
            
        # Search for similar papers, excluding the source paper
        embedding = np.array(paper.embedding)
        results = await self.search_similar_chunks(
            embedding,
            user_id=paper.user_id or "system",
            options=SearchOptions(limit=limit + 1)
        )
        
        # Filter out the source paper
        return [r for r in results if r.paper_id != paper_id][:limit]
        
    async def batch_search(
        self,
        embeddings: List[np.ndarray],
        user_id: str,
        options: SearchOptions = SearchOptions()
    ) -> List[List[SearchResult]]:
        """Perform batch similarity search for multiple embeddings."""
        results = []
        
        # Process in parallel using asyncio
        search_tasks = [
            self.search_similar_chunks(embedding, user_id, options)
            for embedding in embeddings
        ]
        
        batch_results = await asyncio.gather(*search_tasks)
        return batch_results