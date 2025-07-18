"""
Hybrid search service combining BM25 and vector search for improved retrieval.
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging
import math
from collections import Counter, defaultdict
import re
from sqlalchemy import select, text, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np

from app.models.paper_chunk import PaperChunk
from app.models.paper import Paper
from app.services.embedding import EmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Container for search results with multiple scores."""
    paper_id: str
    chunk_id: Optional[str]
    chunk_text: str
    vector_score: float
    bm25_score: float
    hybrid_score: float
    metadata: Dict[str, Any]


class BM25Scorer:
    """BM25 scoring implementation for text retrieval."""
    
    def __init__(
        self,
        k1: float = 1.2,
        b: float = 0.75,
        epsilon: float = 0.25
    ):
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon
        self.avg_doc_length = 0
        self.doc_lengths = {}
        self.doc_freqs = defaultdict(int)
        self.idf_cache = {}
        self.corpus_size = 0
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize text for BM25 scoring."""
        # Convert to lowercase and split on non-word characters
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        # Remove stopwords (basic list, can be expanded)
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        return [token for token in tokens if token not in stopwords and len(token) > 2]
    
    def fit(self, documents: List[Tuple[str, str]]):
        """
        Fit BM25 model on corpus.
        
        Args:
            documents: List of (doc_id, text) tuples
        """
        self.corpus_size = len(documents)
        total_length = 0
        
        for doc_id, text in documents:
            tokens = self.tokenize(text)
            self.doc_lengths[doc_id] = len(tokens)
            total_length += len(tokens)
            
            # Count document frequencies
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freqs[token] += 1
        
        self.avg_doc_length = total_length / self.corpus_size if self.corpus_size > 0 else 0
        
        # Pre-calculate IDF scores
        for token, freq in self.doc_freqs.items():
            self.idf_cache[token] = self._calculate_idf(freq)
    
    def _calculate_idf(self, doc_freq: int) -> float:
        """Calculate IDF score for a term."""
        return math.log((self.corpus_size - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
    
    def score(self, query: str, doc_id: str, doc_text: str) -> float:
        """
        Calculate BM25 score for a document given a query.
        
        Args:
            query: Search query
            doc_id: Document ID
            doc_text: Document text
            
        Returns:
            BM25 score
        """
        query_tokens = self.tokenize(query)
        doc_tokens = self.tokenize(doc_text)
        doc_length = len(doc_tokens)
        
        # Count term frequencies in document
        doc_term_freqs = Counter(doc_tokens)
        
        score = 0.0
        for term in query_tokens:
            if term not in self.idf_cache:
                continue
                
            term_freq = doc_term_freqs.get(term, 0)
            idf = self.idf_cache[term]
            
            # BM25 formula
            numerator = idf * term_freq * (self.k1 + 1)
            denominator = term_freq + self.k1 * (
                1 - self.b + self.b * doc_length / self.avg_doc_length
            )
            
            score += numerator / denominator
        
        return score


class HybridSearchService:
    """Service for hybrid search combining BM25 and vector search."""
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5,
        rerank_top_k: int = 100
    ):
        self.embedding_service = embedding_service
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.rerank_top_k = rerank_top_k
        self.bm25_scorer = BM25Scorer()
        self._is_fitted = False
    
    async def fit_bm25(self, session: AsyncSession):
        """Fit BM25 model on the corpus."""
        # Fetch all chunks for BM25 fitting
        stmt = select(PaperChunk.id, PaperChunk.content)
        result = await session.execute(stmt)
        documents = [(str(chunk_id), content) for chunk_id, content in result]
        
        if documents:
            self.bm25_scorer.fit(documents)
            self._is_fitted = True
            logger.info(f"BM25 model fitted on {len(documents)} documents")
        else:
            logger.warning("No documents found for BM25 fitting")
    
    async def hybrid_search(
        self,
        session: AsyncSession,
        query: str,
        limit: int = 30,
        min_similarity: float = 0.4,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Perform hybrid search combining BM25 and vector search.
        
        Args:
            session: Database session
            query: Search query
            limit: Maximum number of results
            min_similarity: Minimum similarity threshold for vector search
            filters: Optional filters (year range, etc.)
            
        Returns:
            List of search results with hybrid scores
        """
        # Ensure BM25 is fitted
        if not self._is_fitted:
            await self.fit_bm25(session)
        
        # Generate query embedding
        query_embedding = await self.embedding_service.embed_text(query)
        
        # Perform vector search
        vector_results = await self._vector_search(
            session, query_embedding, self.rerank_top_k, min_similarity, filters
        )
        
        # Perform BM25 search
        bm25_results = await self._bm25_search(
            session, query, self.rerank_top_k, filters
        )
        
        # Combine and normalize scores
        combined_results = self._combine_results(vector_results, bm25_results)
        
        # Sort by hybrid score and return top results
        combined_results.sort(key=lambda x: x.hybrid_score, reverse=True)
        return combined_results[:limit]
    
    async def _vector_search(
        self,
        session: AsyncSession,
        query_embedding: List[float],
        limit: int,
        min_similarity: float,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, str, str, float, Dict]]:
        """Perform vector similarity search."""
        # Build the query
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        query_parts = [
            f"1 - (pc.embedding <=> '{embedding_str}'::vector) as similarity"
        ]
        
        # Apply filters
        where_clauses = []
        if filters:
            if 'start_year' in filters:
                where_clauses.append(f"p.publication_year >= {filters['start_year']}")
            if 'end_year' in filters:
                where_clauses.append(f"p.publication_year <= {filters['end_year']}")
        
        where_clause = f"AND {' AND '.join(where_clauses)}" if where_clauses else ""
        
        # Execute query
        query_text = f"""
        SELECT 
            pc.id as chunk_id,
            pc.paper_id,
            pc.content,
            {query_parts[0]},
            p.title,
            p.authors,
            p.publication_year,
            p.abstract
        FROM paper_chunks pc
        JOIN papers p ON pc.paper_id = p.id
        WHERE similarity >= :min_similarity
        {where_clause}
        ORDER BY similarity DESC
        LIMIT :limit
        """
        
        result = await session.execute(
            text(query_text),
            {"min_similarity": min_similarity, "limit": limit}
        )
        
        results = []
        for row in result:
            metadata = {
                'title': row.title,
                'authors': row.authors,
                'year': row.publication_year,
                'abstract': row.abstract
            }
            results.append((
                str(row.chunk_id),
                row.paper_id,
                row.content,
                row.similarity,
                metadata
            ))
        
        return results
    
    async def _bm25_search(
        self,
        session: AsyncSession,
        query: str,
        limit: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, str, str, float, Dict]]:
        """Perform BM25 search."""
        # First, get candidate chunks (can be optimized with inverted index)
        stmt = select(
            PaperChunk.id,
            PaperChunk.paper_id,
            PaperChunk.content,
            Paper.title,
            Paper.authors,
            Paper.publication_year,
            Paper.abstract
        ).join(Paper, PaperChunk.paper_id == Paper.id)
        
        # Apply filters
        if filters:
            if 'start_year' in filters:
                stmt = stmt.where(Paper.publication_year >= filters['start_year'])
            if 'end_year' in filters:
                stmt = stmt.where(Paper.publication_year <= filters['end_year'])
        
        result = await session.execute(stmt)
        
        # Score all chunks with BM25
        scored_results = []
        for row in result:
            chunk_id = str(row.id)
            bm25_score = self.bm25_scorer.score(query, chunk_id, row.content)
            
            if bm25_score > 0:  # Only include chunks with positive scores
                metadata = {
                    'title': row.title,
                    'authors': row.authors,
                    'year': row.publication_year,
                    'abstract': row.abstract
                }
                scored_results.append((
                    chunk_id,
                    row.paper_id,
                    row.content,
                    bm25_score,
                    metadata
                ))
        
        # Sort by BM25 score and return top results
        scored_results.sort(key=lambda x: x[3], reverse=True)
        return scored_results[:limit]
    
    def _combine_results(
        self,
        vector_results: List[Tuple[str, str, str, float, Dict]],
        bm25_results: List[Tuple[str, str, str, float, Dict]]
    ) -> List[SearchResult]:
        """Combine vector and BM25 results with score normalization."""
        # Create dictionaries for easy lookup
        vector_dict = {chunk_id: (paper_id, content, score, metadata) 
                      for chunk_id, paper_id, content, score, metadata in vector_results}
        bm25_dict = {chunk_id: (paper_id, content, score, metadata)
                    for chunk_id, paper_id, content, score, metadata in bm25_results}
        
        # Get all unique chunk IDs
        all_chunk_ids = set(vector_dict.keys()) | set(bm25_dict.keys())
        
        # Normalize scores
        max_vector_score = max([score for _, _, _, score, _ in vector_results], default=1.0)
        max_bm25_score = max([score for _, _, _, score, _ in bm25_results], default=1.0)
        
        combined_results = []
        for chunk_id in all_chunk_ids:
            # Get scores (default to 0 if not present)
            vector_score = 0.0
            bm25_score = 0.0
            paper_id = None
            content = None
            metadata = {}
            
            if chunk_id in vector_dict:
                paper_id, content, vector_score, metadata = vector_dict[chunk_id]
                vector_score = vector_score / max_vector_score if max_vector_score > 0 else 0
            
            if chunk_id in bm25_dict:
                paper_id_bm25, content_bm25, bm25_score_raw, metadata_bm25 = bm25_dict[chunk_id]
                bm25_score = bm25_score_raw / max_bm25_score if max_bm25_score > 0 else 0
                
                # Use BM25 data if vector data is missing
                if paper_id is None:
                    paper_id = paper_id_bm25
                    content = content_bm25
                    metadata = metadata_bm25
            
            # Calculate hybrid score
            hybrid_score = (
                self.vector_weight * vector_score +
                self.bm25_weight * bm25_score
            )
            
            combined_results.append(SearchResult(
                paper_id=paper_id,
                chunk_id=chunk_id,
                chunk_text=content,
                vector_score=vector_score,
                bm25_score=bm25_score,
                hybrid_score=hybrid_score,
                metadata=metadata
            ))
        
        return combined_results
    
    def update_weights(self, vector_weight: float, bm25_weight: float):
        """Update the weights for hybrid scoring."""
        if abs(vector_weight + bm25_weight - 1.0) > 0.001:
            # Normalize weights
            total = vector_weight + bm25_weight
            vector_weight = vector_weight / total
            bm25_weight = bm25_weight / total
        
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight