"""Unit tests for citation engine services."""
import pytest
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.services.text_analysis import TextAnalysisService, TextContext
from app.services.embedding import EmbeddingService
from app.services.vector_search import VectorSearchService, SearchOptions, SearchResult
from app.services.citation_engine import RankingService, CitationEngine


class TestTextAnalysisService:
    """Tests for text analysis service."""
    
    def setup_method(self):
        self.service = TextAnalysisService()
    
    def test_extract_sentences(self):
        """Test sentence extraction."""
        text = "First sentence. Second sentence! Third sentence?"
        sentences = self.service._extract_sentences(text)
        assert len(sentences) == 3
        assert sentences[0] == "First sentence."
        assert sentences[1] == "Second sentence!"
        assert sentences[2] == "Third sentence?"
    
    def test_extract_context_with_cursor(self):
        """Test context extraction with cursor position."""
        text = "This is sentence one. This is sentence two. This is sentence three."
        context = self.service.extract_context(text, {"cursorPosition": 25})
        
        assert "sentence two" in context.current_sentence
        assert "sentence one" in context.previous_sentence
        assert "sentence three" in context.next_sentence
    
    def test_preprocess_text(self):
        """Test text preprocessing."""
        # Test whitespace normalization
        assert self.service.preprocess_text("  multiple   spaces  ") == "multiple spaces"
        
        # Test special character handling
        assert self.service.preprocess_text("test@#$%text") == "testtext"
        
        # Test punctuation preservation
        assert "." in self.service.preprocess_text("End of sentence.")
        assert "?" in self.service.preprocess_text("Question?")
    
    def test_should_update_suggestions(self):
        """Test suggestion update logic."""
        # No change
        assert not self.service.should_update_suggestions("test", "test")
        
        # Minor change (punctuation)
        assert not self.service.should_update_suggestions("test", "test.")
        
        # Significant change
        assert self.service.should_update_suggestions("old text", "completely new text")
        
        # Length-based change
        assert self.service.should_update_suggestions("short", "this is a much longer text now")


class TestEmbeddingService:
    """Tests for embedding service."""
    
    @pytest.mark.asyncio
    async def test_generate_embedding(self):
        """Test embedding generation."""
        service = EmbeddingService()
        text = "Test text for embedding"
        
        embedding = await service.generate_embedding(text)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,)  # all-MiniLM-L6-v2 dimension
        assert embedding.dtype == np.float32
    
    @pytest.mark.asyncio
    async def test_batch_embeddings(self):
        """Test batch embedding generation."""
        service = EmbeddingService()
        texts = ["First text", "Second text", "Third text"]
        
        embeddings = await service.generate_batch_embeddings(texts)
        
        assert len(embeddings) == 3
        assert all(isinstance(emb, np.ndarray) for emb in embeddings)
        assert all(emb.shape == (384,) for emb in embeddings)
    
    def test_caching(self):
        """Test embedding caching."""
        service = EmbeddingService()
        text = "Cached text"
        
        # Generate hash
        text_hash = service._text_to_hash(text)
        assert isinstance(text_hash, str)
        assert len(text_hash) == 32  # MD5 hash length
        
        # Test cache miss
        cached = service.get_cached_embedding(text)
        assert cached is None
    
    @pytest.mark.asyncio
    async def test_empty_batch(self):
        """Test handling of empty batch."""
        service = EmbeddingService()
        embeddings = await service.generate_batch_embeddings([])
        assert embeddings == []


class TestVectorSearchService:
    """Tests for vector search service."""
    
    @pytest.mark.asyncio
    async def test_search_similar_chunks(self):
        """Test vector similarity search."""
        # Mock database session
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            Mock(
                id="paper1",
                title="Test Paper 1",
                authors=["Author 1"],
                year=2023,
                abstract="Abstract 1",
                chunk_text="Chunk 1",
                chunk_index=0,
                metadata={},
                similarity=0.95
            )
        ]
        mock_db.execute.return_value = mock_result
        
        service = VectorSearchService(mock_db)
        embedding = np.random.rand(384).astype(np.float32)
        
        results = await service.search_similar_chunks(
            embedding=embedding,
            user_id="test-user",
            options=SearchOptions(limit=5, min_similarity=0.5)
        )
        
        assert len(results) == 1
        assert results[0].paper_id == "paper1"
        assert results[0].similarity == 0.95
    
    def test_search_options(self):
        """Test search options configuration."""
        options = SearchOptions(
            limit=20,
            min_similarity=0.7,
            filters={
                "year_from": 2020,
                "year_to": 2023,
                "paper_type": ["conference", "journal"]
            }
        )
        
        assert options.limit == 20
        assert options.min_similarity == 0.7
        assert options.filters["year_from"] == 2020


class TestRankingService:
    """Tests for ranking service."""
    
    def setup_method(self):
        self.service = RankingService()
    
    def test_calculate_relevance(self):
        """Test relevance calculation."""
        search_result = SearchResult(
            paper_id="test",
            title="Machine Learning for NLP",
            authors=["Smith, J."],
            year=2023,
            abstract="Abstract about machine learning",
            similarity=0.9,
            chunk_text="Machine learning techniques",
            chunk_index=0,
            metadata={"citation_count": 150, "venue_rank": "A"}
        )
        
        context = TextContext(
            current_sentence="I'm writing about machine learning",
            previous_sentence="NLP has evolved significantly",
            paragraph="NLP has evolved. I'm writing about machine learning."
        )
        
        relevance = self.service.calculate_relevance(search_result, context)
        
        assert 0 <= relevance <= 1
        assert relevance > 0.5  # Should be reasonably high given the match
    
    def test_recency_score(self):
        """Test recency scoring."""
        current_year = datetime.now().year
        
        # Very recent paper
        assert self.service._calculate_recency_score(current_year) == 1.0
        
        # 3 years old
        assert 0.7 < self.service._calculate_recency_score(current_year - 3) < 0.9
        
        # 10 years old
        assert 0.5 < self.service._calculate_recency_score(current_year - 10) < 0.7
        
        # Very old paper
        assert self.service._calculate_recency_score(current_year - 50) >= 0.3
    
    def test_quality_score(self):
        """Test quality scoring."""
        # High quality paper
        high_quality = SearchResult(
            paper_id="1", title="Title", authors=[], year=2023,
            abstract="", similarity=0.9, chunk_text="", chunk_index=0,
            metadata={"citation_count": 500, "venue_rank": "A+"}
        )
        assert self.service._calculate_quality_score(high_quality) > 0.8
        
        # Medium quality
        medium_quality = SearchResult(
            paper_id="2", title="Title", authors=[], year=2023,
            abstract="", similarity=0.9, chunk_text="", chunk_index=0,
            metadata={"citation_count": 50, "venue_rank": "B"}
        )
        assert 0.5 < self.service._calculate_quality_score(medium_quality) < 0.8
    
    def test_rank_results(self):
        """Test result ranking."""
        results = [
            SearchResult(
                paper_id="1", title="Highly Relevant Paper",
                authors=["A"], year=2023, abstract="Very relevant",
                similarity=0.95, chunk_text="Exact match",
                chunk_index=0, metadata={"citation_count": 1000}
            ),
            SearchResult(
                paper_id="2", title="Less Relevant Paper",
                authors=["B"], year=2020, abstract="Somewhat relevant",
                similarity=0.65, chunk_text="Partial match",
                chunk_index=0, metadata={"citation_count": 10}
            )
        ]
        
        context = TextContext(current_sentence="Looking for exact match", paragraph="")
        citations = self.service.rank_results(results, context)
        
        assert len(citations) > 0
        assert citations[0].paper_id == "1"  # Higher relevance should be first
        assert citations[0].confidence > citations[1].confidence if len(citations) > 1 else True


@pytest.mark.asyncio
async def test_citation_engine_integration():
    """Test citation engine integration."""
    # Mock database
    mock_db = AsyncMock()
    
    # Mock vector search to return results
    with patch('app.services.vector_search.VectorSearchService.search_similar_chunks') as mock_search:
        mock_search.return_value = [
            SearchResult(
                paper_id="test-paper",
                title="Test Paper for Citations",
                authors=["Test Author"],
                year=2023,
                abstract="This is a test abstract",
                similarity=0.88,
                chunk_text="Test chunk text",
                chunk_index=0,
                metadata={"citation_count": 100}
            )
        ]
        
        engine = CitationEngine(mock_db)
        context = TextContext(
            current_sentence="Writing about test topics",
            paragraph="This is a test paragraph"
        )
        
        suggestions = await engine.get_suggestions(
            text="Writing about test topics",
            context=context,
            user_id="test-user"
        )
        
        assert len(suggestions) > 0
        assert suggestions[0].title == "Test Paper for Citations"
        assert suggestions[0].confidence > 0.5
        assert suggestions[0].display_text == "(Test Author, 2023)"