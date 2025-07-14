"""Citation engine for generating contextual paper suggestions."""
import numpy as np
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.embedding import EmbeddingService
from app.services.vector_search_v2 import VectorSearchService, SearchOptions, SearchResult
from app.services.text_analysis import TextContext
from app.core.config import settings
import logging
import asyncio
from datetime import datetime
import redis.asyncio as redis

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """Represents a citation suggestion."""
    paper_id: str
    title: str
    authors: List[str]
    year: int
    abstract: str
    confidence: float
    citation_style: str = "inline"  # inline or footnote
    display_text: str = ""
    relevance_scores: Dict[str, float] = None


class RankingService:
    """Service for ranking and scoring citation suggestions."""
    
    def calculate_relevance(self, search_result: SearchResult, context: TextContext) -> float:
        """Calculate overall relevance score for a citation."""
        # Base similarity from vector search (40% weight)
        similarity_score = search_result.similarity * 0.4
        
        # Contextual relevance (25% weight)
        context_score = self._calculate_context_score(search_result, context) * 0.25
        
        # Paper quality metrics (15% weight)
        quality_score = self._calculate_quality_score(search_result) * 0.15
        
        # Recency bias (10% weight)
        recency_score = self._calculate_recency_score(search_result.year) * 0.1
        
        # User preference score (10% weight) - placeholder for now
        preference_score = 0.5 * 0.1
        
        total_score = similarity_score + context_score + quality_score + recency_score + preference_score
        
        return min(max(total_score, 0.0), 1.0)  # Clamp between 0 and 1
        
    def _calculate_context_score(self, result: SearchResult, context: TextContext) -> float:
        """Calculate how well the result fits the surrounding context."""
        score = 0.5  # Base score
        
        # Check if previous/next sentences mention similar concepts
        if context.previous_sentence:
            # Simple keyword matching for now
            prev_words = set(context.previous_sentence.lower().split())
            title_words = set(result.title.lower().split())
            overlap = len(prev_words & title_words)
            score += min(overlap * 0.1, 0.3)
            
        # Check paragraph relevance
        if context.paragraph:
            para_words = set(context.paragraph.lower().split())
            abstract_words = set(result.abstract.lower().split()[:50])  # First 50 words
            overlap = len(para_words & abstract_words)
            score += min(overlap * 0.02, 0.2)
            
        return score
        
    def _calculate_quality_score(self, result: SearchResult) -> float:
        """Calculate paper quality score based on metadata."""
        score = 0.5  # Base score
        
        # Check if paper has complete metadata
        if result.metadata:
            if result.metadata.get("citation_count", 0) > 100:
                score += 0.3
            elif result.metadata.get("citation_count", 0) > 10:
                score += 0.2
                
            if result.metadata.get("venue_rank", "C") in ["A", "A+"]:
                score += 0.2
            elif result.metadata.get("venue_rank", "C") == "B":
                score += 0.1
                
        return min(score, 1.0)
        
    def _calculate_recency_score(self, year: int) -> float:
        """Calculate recency score with bias towards recent papers."""
        current_year = datetime.now().year
        age = current_year - year
        
        if age <= 2:
            return 1.0
        elif age <= 5:
            return 0.8
        elif age <= 10:
            return 0.6
        else:
            return max(0.3, 1.0 - (age * 0.02))  # Decrease by 2% per year, min 0.3
            
    def rank_results(self, results: List[SearchResult], context: TextContext) -> List[Citation]:
        """Rank search results and convert to citations."""
        citations = []
        
        for result in results:
            relevance = self.calculate_relevance(result, context)
            
            # Determine confidence level
            if relevance > 0.85:
                confidence = "high"
            elif relevance > 0.70:
                confidence = "medium"
            elif relevance > 0.50:
                confidence = "low"
            else:
                continue  # Filter out very low confidence
                
            # Generate display text
            display_text = self._generate_display_text(result)
            
            citation = Citation(
                paper_id=result.paper_id,
                title=result.title,
                authors=result.authors,
                year=result.year,
                abstract=result.abstract,
                confidence=relevance,
                display_text=display_text,
                relevance_scores={
                    "similarity": result.similarity,
                    "context": self._calculate_context_score(result, context),
                    "quality": self._calculate_quality_score(result),
                    "recency": self._calculate_recency_score(result.year)
                }
            )
            citations.append(citation)
            
        # Sort by confidence
        citations.sort(key=lambda x: x.confidence, reverse=True)
        
        return citations
        
    def _generate_display_text(self, result: SearchResult) -> str:
        """Generate the display text for inline citation."""
        # Simple format: (First Author et al., Year)
        if result.authors:
            first_author = result.authors[0].split()[-1]  # Last name
            if len(result.authors) > 1:
                return f"({first_author} et al., {result.year})"
            else:
                return f"({first_author}, {result.year})"
        else:
            return f"(Unknown, {result.year})"


class CitationEngine:
    """Main engine for generating citation suggestions."""
    
    def __init__(self, db: AsyncSession):
        """Initialize the citation engine."""
        self.db = db
        self.embedding_service = EmbeddingService()
        self.vector_search = VectorSearchService(db)
        self.ranking_service = RankingService()
        
        # Initialize Redis for caching (optional)
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
            
    async def get_suggestions(
        self,
        text: str,
        context: TextContext,
        user_id: str,
        options: Optional[SearchOptions] = None
    ) -> List[Citation]:
        """Get citation suggestions for the given text and context."""
        
        # Use default options if not provided
        if options is None:
            options = SearchOptions(limit=20, min_similarity=0.5)
            
        # Check cache first
        cache_key = f"citations:{user_id}:{hash(text)}"
        if self.redis_client:
            try:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    logger.info("Returning cached citation suggestions")
                    # TODO: Deserialize cached citations
                    pass
            except Exception as e:
                logger.warning(f"Cache retrieval failed: {e}")
                
        # Generate embedding for the text
        embedding = await self.embedding_service.generate_embedding(text)
        
        # Search for similar papers
        search_results = await self.vector_search.search_similar_chunks(
            embedding=embedding,
            user_id=user_id,
            options=options
        )
        
        # Rank and filter results
        citations = self.ranking_service.rank_results(search_results, context)
        
        # Limit to top results
        citations = citations[:10]
        
        # Cache the results
        if self.redis_client and citations:
            try:
                # TODO: Serialize citations for caching
                await self.redis_client.setex(
                    cache_key,
                    3600,  # 1 hour TTL
                    "cached_data"  # Placeholder
                )
            except Exception as e:
                logger.warning(f"Cache storage failed: {e}")
                
        logger.info(f"Generated {len(citations)} citation suggestions for user {user_id}")
        return citations
        
    async def batch_get_suggestions(
        self,
        texts: List[str],
        contexts: List[TextContext],
        user_id: str
    ) -> List[List[Citation]]:
        """Get suggestions for multiple texts in batch."""
        # Generate embeddings in batch
        embeddings = await self.embedding_service.generate_batch_embeddings(texts)
        
        # Search for each embedding
        search_tasks = [
            self.vector_search.search_similar_chunks(
                embedding=emb,
                user_id=user_id,
                options=SearchOptions(limit=10)
            )
            for emb in embeddings
        ]
        
        all_results = await asyncio.gather(*search_tasks)
        
        # Rank results for each context
        all_citations = []
        for results, context in zip(all_results, contexts):
            citations = self.ranking_service.rank_results(results, context)
            all_citations.append(citations[:5])  # Top 5 per text
            
        return all_citations
        
    async def close(self):
        """Clean up resources."""
        if self.redis_client:
            await self.redis_client.close()