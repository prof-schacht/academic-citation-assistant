"""
Enhanced citation engine with hybrid search and reranking capabilities.
"""
import numpy as np
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.embedding import EmbeddingService
from app.services.vector_search_v2 import VectorSearchService, SearchOptions, SearchResult
from app.services.hybrid_search import HybridSearchService
from app.services.reranking_service import RerankingService, RerankingResult
from app.services.text_analysis import TextContext
from app.core.config import settings
import logging
import asyncio
from datetime import datetime
import redis.asyncio as redis

logger = logging.getLogger(__name__)


from app.services.citation_engine import Citation, RankingService

@dataclass
class EnhancedCitation(Citation):
    """Enhanced citation with additional ranking information."""
    bm25_score: float = 0.0
    rerank_score: float = 0.0
    hybrid_score: float = 0.0
    chunk_type: str = ""  # abstract, intro, methods, etc.
    sentence_count: int = 0


class EnhancedCitationEngine:
    """Enhanced citation engine with hybrid search and reranking."""
    
    def __init__(self, db: AsyncSession):
        """Initialize the enhanced citation engine."""
        self.db = db
        self.embedding_service = EmbeddingService()
        self.vector_search = VectorSearchService(db)
        self.ranking_service = RankingService()
        
        # Initialize new services
        self.hybrid_search = HybridSearchService(
            embedding_service=self.embedding_service,
            vector_weight=0.6,
            bm25_weight=0.4,
            rerank_top_k=150  # Get more candidates for reranking
        )
        
        self.reranking_service = RerankingService(
            cross_encoder_model='ms-marco-MiniLM',
            rerank_weight=0.7,
            original_weight=0.3,
            context_weight=0.2
        )
        
        # Initialize Redis for caching
        self.redis_client = None
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection for caching."""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        except Exception as e:
            logger.warning(f"Redis not available for caching: {e}")
            self.redis_client = None
    
    async def get_suggestions_enhanced(
        self,
        text: str,
        context: TextContext,
        user_id: str,
        options: Optional[SearchOptions] = None,
        use_reranking: bool = True,
        search_strategy: str = "hybrid"  # "vector", "bm25", or "hybrid"
    ) -> List[EnhancedCitation]:
        """
        Get enhanced citation suggestions with hybrid search and reranking.
        
        Args:
            text: The text to find citations for
            context: Surrounding context
            user_id: User identifier
            options: Search options
            use_reranking: Whether to apply cross-encoder reranking
            search_strategy: Which search strategy to use
            
        Returns:
            List of enhanced citations
        """
        # Use default options if not provided
        if options is None:
            options = SearchOptions(
                limit=150 if use_reranking else 50,  # Get more for reranking
                min_similarity=0.35  # Lower threshold, let reranker decide
            )
        
        # Check cache first
        cache_key = f"citations_v2:{user_id}:{hash(text)}:{search_strategy}:{use_reranking}"
        if self.redis_client:
            try:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    logger.info("Returning cached enhanced citation suggestions")
                    # TODO: Deserialize cached citations
                    pass
            except Exception as e:
                logger.warning(f"Cache retrieval failed: {e}")
        
        # Get search results based on strategy
        if search_strategy == "hybrid":
            search_results = await self._hybrid_search(text, options)
        elif search_strategy == "bm25":
            search_results = await self._bm25_search(text, options)
        else:  # vector
            search_results = await self._vector_search(text, options)
        
        # Apply reranking if requested
        if use_reranking and search_results:
            reranked_results = await self._rerank_results(text, context, search_results)
            citations = self._convert_to_enhanced_citations(reranked_results, context)
        else:
            # Use traditional ranking
            citations = self._apply_traditional_ranking(search_results, context)
        
        # Filter low confidence results
        citations = [c for c in citations if c.confidence > 0.5]
        
        # Limit to top results
        citations = citations[:15]  # Return more than before due to better quality
        
        # Cache results
        if self.redis_client and citations:
            try:
                # TODO: Serialize and cache citations
                await self.redis_client.setex(
                    cache_key,
                    3600,  # 1 hour TTL
                    str(len(citations))  # Placeholder
                )
            except Exception as e:
                logger.warning(f"Cache storage failed: {e}")
        
        return citations
    
    async def _hybrid_search(
        self, text: str, options: SearchOptions
    ) -> List[Dict[str, Any]]:
        """Perform hybrid BM25 + vector search."""
        # Ensure BM25 index is fitted
        if not self.hybrid_search._is_fitted:
            await self.hybrid_search.fit_bm25(self.db)
        
        # Perform hybrid search
        results = await self.hybrid_search.hybrid_search(
            session=self.db,
            query=text,
            limit=options.limit,
            min_similarity=options.min_similarity,
            filters={
                'start_year': options.year_range[0] if options.year_range else None,
                'end_year': options.year_range[1] if options.year_range else None
            }
        )
        
        # Convert to dict format for compatibility
        return [
            {
                'paper_id': r.paper_id,
                'chunk_id': r.chunk_id,
                'chunk_text': r.chunk_text,
                'score': r.hybrid_score,
                'hybrid_score': r.hybrid_score,
                'vector_score': r.vector_score,
                'bm25_score': r.bm25_score,
                'metadata': r.metadata
            }
            for r in results
        ]
    
    async def _vector_search(
        self, text: str, options: SearchOptions
    ) -> List[Dict[str, Any]]:
        """Perform traditional vector search."""
        embedding = await self.embedding_service.generate_embedding(text)
        
        results = await self.vector_search.search_similar_chunks(
            embedding=embedding,
            user_id="",  # Not using user-specific search for now
            options=options
        )
        
        # Convert SearchResult to dict format
        return [
            {
                'paper_id': r.paper_id,
                'chunk_id': r.metadata.get('chunk_id', ''),
                'chunk_text': r.chunk_text,
                'score': r.similarity,
                'vector_score': r.similarity,
                'metadata': {
                    'title': r.title,
                    'authors': r.authors,
                    'year': r.year,
                    'abstract': r.abstract,
                    **r.metadata
                }
            }
            for r in results
        ]
    
    async def _bm25_search(
        self, text: str, options: SearchOptions
    ) -> List[Dict[str, Any]]:
        """Perform BM25-only search."""
        # This would need implementation in hybrid_search service
        # For now, fall back to hybrid with heavy BM25 weight
        self.hybrid_search.update_weights(vector_weight=0.1, bm25_weight=0.9)
        results = await self._hybrid_search(text, options)
        # Reset weights
        self.hybrid_search.update_weights(vector_weight=0.6, bm25_weight=0.4)
        return results
    
    async def _rerank_results(
        self,
        query: str,
        context: TextContext,
        results: List[Dict[str, Any]]
    ) -> List[RerankingResult]:
        """Apply cross-encoder reranking to search results."""
        # Prepare context for reranking
        query_context = {
            'current': context.current_sentence,
            'previous': context.previous_sentence,
            'next': context.next_sentence
        }
        
        # Rerank results
        reranked = await self.reranking_service.rerank_results(
            query=query,
            results=results,
            query_context=query_context,
            top_k=50  # Rerank top 50
        )
        
        return reranked
    
    def _convert_to_enhanced_citations(
        self,
        reranked_results: List[RerankingResult],
        context: TextContext
    ) -> List[EnhancedCitation]:
        """Convert reranked results to enhanced citations."""
        citations = []
        
        for result in reranked_results:
            metadata = result.metadata
            
            citation = EnhancedCitation(
                paper_id=result.paper_id,
                title=metadata.get('title', ''),
                authors=metadata.get('authors', []),
                year=metadata.get('year', 0),
                abstract=metadata.get('abstract', ''),
                confidence=result.final_score,
                display_text=self._generate_display_text(metadata),
                relevance_scores={
                    "original": result.original_score,
                    "rerank": result.rerank_score,
                    "final": result.final_score,
                    "context": result.context_match or 0.0
                },
                chunk_text=result.chunk_text,
                chunk_index=metadata.get('chunk_index', 0),
                chunk_id=result.chunk_id or '',
                section_title=metadata.get('section', ''),
                bm25_score=result.original_score,  # Assuming original is hybrid score
                rerank_score=result.rerank_score,
                hybrid_score=result.original_score,
                chunk_type=metadata.get('chunk_type', ''),
                sentence_count=metadata.get('sentence_count', 0)
            )
            citations.append(citation)
        
        return citations
    
    def _apply_traditional_ranking(
        self,
        results: List[Dict[str, Any]],
        context: TextContext
    ) -> List[EnhancedCitation]:
        """Apply traditional ranking without reranking."""
        # Convert to SearchResult format for compatibility
        search_results = []
        for r in results:
            metadata = r.get('metadata', {})
            sr = SearchResult(
                paper_id=r['paper_id'],
                title=metadata.get('title', ''),
                authors=metadata.get('authors', []),
                year=metadata.get('year', 0),
                abstract=metadata.get('abstract', ''),
                similarity=r.get('score', 0.0),
                chunk_text=r.get('chunk_text', ''),
                chunk_index=metadata.get('chunk_index', 0),
                metadata=metadata
            )
            search_results.append(sr)
        
        # Use existing ranking service
        basic_citations = self.ranking_service.rank_results(search_results, context)
        
        # Convert to enhanced citations
        enhanced_citations = []
        for i, (citation, result) in enumerate(zip(basic_citations, results)):
            enhanced = EnhancedCitation(
                paper_id=citation.paper_id,
                title=citation.title,
                authors=citation.authors,
                year=citation.year,
                abstract=citation.abstract,
                confidence=citation.confidence,
                display_text=citation.display_text,
                relevance_scores=citation.relevance_scores,
                chunk_text=citation.chunk_text,
                chunk_index=citation.chunk_index,
                chunk_id=citation.chunk_id,
                section_title=citation.section_title,
                bm25_score=result.get('bm25_score', 0.0),
                rerank_score=0.0,  # Not reranked
                hybrid_score=result.get('hybrid_score', result.get('score', 0.0)),
                chunk_type=result.get('metadata', {}).get('chunk_type', ''),
                sentence_count=result.get('metadata', {}).get('sentence_count', 0)
            )
            enhanced_citations.append(enhanced)
        
        return enhanced_citations
    
    def _generate_display_text(self, metadata: Dict[str, Any]) -> str:
        """Generate the display text for inline citation."""
        authors = metadata.get('authors', [])
        year = metadata.get('year', 0)
        
        if authors:
            first_author = authors[0].split()[-1]  # Last name
            if len(authors) > 1:
                return f"({first_author} et al., {year})"
            else:
                return f"({first_author}, {year})"
        else:
            return f"(Unknown, {year})"