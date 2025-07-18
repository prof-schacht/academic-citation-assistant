"""Tests for hybrid search functionality."""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np

from app.services.hybrid_search import (
    BM25Scorer,
    HybridSearchService,
    SearchResult
)
from app.services.embedding import EmbeddingService


class TestBM25Scorer:
    """Test suite for BM25 scoring."""
    
    @pytest.fixture
    def bm25_scorer(self):
        """Create a BM25 scorer instance."""
        return BM25Scorer()
    
    def test_tokenization(self, bm25_scorer):
        """Test text tokenization."""
        text = "The quick brown fox jumps over the lazy dog."
        tokens = bm25_scorer.tokenize(text)
        
        # Should remove stopwords and short tokens
        assert "the" not in tokens
        assert "quick" in tokens
        assert "brown" in tokens
        assert "fox" in tokens
    
    def test_fit_corpus(self, bm25_scorer):
        """Test fitting BM25 on a corpus."""
        documents = [
            ("doc1", "machine learning algorithms for natural language processing"),
            ("doc2", "deep learning models transform text analysis"),
            ("doc3", "neural networks revolutionize machine translation")
        ]
        
        bm25_scorer.fit(documents)
        
        # Verify corpus statistics
        assert bm25_scorer.corpus_size == 3
        assert bm25_scorer.avg_doc_length > 0
        assert len(bm25_scorer.doc_lengths) == 3
        assert len(bm25_scorer.idf_cache) > 0
    
    def test_scoring(self, bm25_scorer):
        """Test BM25 scoring."""
        documents = [
            ("doc1", "machine learning algorithms for natural language processing"),
            ("doc2", "deep learning models transform text analysis"),
            ("doc3", "neural networks revolutionize machine translation")
        ]
        
        bm25_scorer.fit(documents)
        
        # Score a query against documents
        query = "machine learning translation"
        
        score1 = bm25_scorer.score(query, "doc1", documents[0][1])
        score2 = bm25_scorer.score(query, "doc2", documents[1][1])
        score3 = bm25_scorer.score(query, "doc3", documents[2][1])
        
        # Doc1 and Doc3 should score higher (contain "machine")
        assert score1 > 0
        assert score3 > 0
        assert score1 > score2 or score3 > score2


class TestHybridSearchService:
    """Test suite for hybrid search service."""
    
    @pytest.fixture
    def mock_embedding_service(self):
        """Create a mock embedding service."""
        service = Mock(spec=EmbeddingService)
        service.embed_text = AsyncMock(return_value=[0.1] * 384)
        return service
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return Mock(spec=AsyncSession)
    
    @pytest.fixture
    def hybrid_search(self, mock_embedding_service):
        """Create a hybrid search service."""
        return HybridSearchService(
            embedding_service=mock_embedding_service,
            vector_weight=0.5,
            bm25_weight=0.5
        )
    
    @pytest.mark.asyncio
    async def test_fit_bm25_empty_corpus(self, hybrid_search, mock_session):
        """Test fitting BM25 with empty corpus."""
        # Mock empty result
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([]))
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        await hybrid_search.fit_bm25(mock_session)
        
        # Should handle empty corpus gracefully
        assert not hybrid_search._is_fitted
    
    @pytest.mark.asyncio
    async def test_combine_results(self, hybrid_search):
        """Test combining vector and BM25 results."""
        vector_results = [
            ("chunk1", "paper1", "Content 1", 0.9, {"title": "Paper 1"}),
            ("chunk2", "paper2", "Content 2", 0.8, {"title": "Paper 2"}),
        ]
        
        bm25_results = [
            ("chunk2", "paper2", "Content 2", 5.0, {"title": "Paper 2"}),
            ("chunk3", "paper3", "Content 3", 4.0, {"title": "Paper 3"}),
        ]
        
        combined = hybrid_search._combine_results(vector_results, bm25_results)
        
        # Should have all unique chunks
        assert len(combined) == 3
        
        # Check that scores are normalized and combined
        chunk_ids = [r.chunk_id for r in combined]
        assert "chunk1" in chunk_ids
        assert "chunk2" in chunk_ids
        assert "chunk3" in chunk_ids
        
        # chunk2 should have highest score (present in both)
        chunk2_result = next(r for r in combined if r.chunk_id == "chunk2")
        assert chunk2_result.vector_score > 0
        assert chunk2_result.bm25_score > 0
        assert chunk2_result.hybrid_score > 0
    
    def test_weight_normalization(self, mock_embedding_service):
        """Test weight normalization."""
        # Create with non-normalized weights
        service = HybridSearchService(
            embedding_service=mock_embedding_service,
            vector_weight=0.7,
            bm25_weight=0.5
        )
        
        # Weights should be normalized
        assert abs(service.vector_weight + service.bm25_weight - 1.0) < 0.001
    
    def test_update_weights(self, hybrid_search):
        """Test updating search weights."""
        hybrid_search.update_weights(vector_weight=0.3, bm25_weight=0.7)
        
        assert hybrid_search.vector_weight == 0.3
        assert hybrid_search.bm25_weight == 0.7
        
        # Test normalization when sum != 1
        hybrid_search.update_weights(vector_weight=2, bm25_weight=3)
        assert abs(hybrid_search.vector_weight - 0.4) < 0.001
        assert abs(hybrid_search.bm25_weight - 0.6) < 0.001


class TestSearchResult:
    """Test SearchResult dataclass."""
    
    def test_search_result_creation(self):
        """Test creating a SearchResult."""
        result = SearchResult(
            paper_id="paper123",
            chunk_id="chunk456",
            chunk_text="This is the chunk text",
            vector_score=0.85,
            bm25_score=3.2,
            hybrid_score=0.75,
            metadata={"title": "Test Paper", "year": 2024}
        )
        
        assert result.paper_id == "paper123"
        assert result.chunk_id == "chunk456"
        assert result.vector_score == 0.85
        assert result.bm25_score == 3.2
        assert result.hybrid_score == 0.75
        assert result.metadata["title"] == "Test Paper"
        assert result.metadata["year"] == 2024


class TestHybridSearchIntegration:
    """Integration tests for hybrid search."""
    
    @pytest.mark.asyncio
    async def test_hybrid_search_full_flow(self, mock_session):
        """Test full hybrid search flow."""
        # Create real embedding service (or mock if needed)
        embedding_service = Mock(spec=EmbeddingService)
        embedding_service.embed_text = AsyncMock(return_value=[0.1] * 384)
        
        hybrid_search = HybridSearchService(embedding_service)
        
        # Mock vector search results
        with patch.object(hybrid_search, '_vector_search') as mock_vector:
            mock_vector.return_value = [
                ("chunk1", "paper1", "Neural networks for NLP", 0.9, {"title": "Paper 1"}),
                ("chunk2", "paper2", "Deep learning advances", 0.85, {"title": "Paper 2"}),
            ]
            
            # Mock BM25 search results
            with patch.object(hybrid_search, '_bm25_search') as mock_bm25:
                mock_bm25.return_value = [
                    ("chunk2", "paper2", "Deep learning advances", 4.5, {"title": "Paper 2"}),
                    ("chunk3", "paper3", "Machine learning review", 3.8, {"title": "Paper 3"}),
                ]
                
                # Mock BM25 fitting
                hybrid_search._is_fitted = True
                
                # Perform hybrid search
                results = await hybrid_search.hybrid_search(
                    session=mock_session,
                    query="deep learning neural networks",
                    limit=10
                )
                
                # Verify results
                assert len(results) > 0
                assert all(isinstance(r, SearchResult) for r in results)
                
                # Check that results are sorted by hybrid score
                scores = [r.hybrid_score for r in results]
                assert scores == sorted(scores, reverse=True)