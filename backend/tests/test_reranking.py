"""Tests for the reranking service."""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import torch
import numpy as np

from app.services.reranking_service import (
    CrossEncoderReranker,
    RerankingService,
    RerankingResult
)


class TestCrossEncoderReranker:
    """Test suite for cross-encoder reranking."""
    
    @pytest.fixture
    def mock_model(self):
        """Create a mock transformer model."""
        model = Mock()
        model.to = Mock(return_value=model)
        model.eval = Mock()
        
        # Mock model output
        logits = torch.tensor([[0.2, 0.8]])  # Binary classification scores
        output = Mock()
        output.logits = logits
        model.return_value = output
        
        return model
    
    @pytest.fixture
    def mock_tokenizer(self):
        """Create a mock tokenizer."""
        tokenizer = Mock()
        
        # Mock tokenizer output
        inputs = {
            'input_ids': torch.tensor([[101, 102, 103]]),
            'attention_mask': torch.tensor([[1, 1, 1]])
        }
        tokenizer.return_value = Mock(
            to=Mock(return_value=inputs),
            **inputs
        )
        
        return tokenizer
    
    @pytest.fixture
    def reranker(self, mock_model, mock_tokenizer):
        """Create a reranker with mocked components."""
        with patch('app.services.reranking_service.AutoTokenizer') as mock_tok_class:
            with patch('app.services.reranking_service.AutoModelForSequenceClassification') as mock_model_class:
                mock_tok_class.from_pretrained.return_value = mock_tokenizer
                mock_model_class.from_pretrained.return_value = mock_model
                
                reranker = CrossEncoderReranker(
                    model_name='ms-marco-MiniLM',
                    device='cpu'
                )
                
                return reranker
    
    def test_initialization(self, reranker):
        """Test reranker initialization."""
        assert reranker.model_name == CrossEncoderReranker.MODELS['ms-marco-MiniLM']
        assert reranker.device == 'cpu'
        assert reranker.max_length == 512
        assert reranker.batch_size == 32
    
    def test_score_single(self, reranker):
        """Test scoring a single query-text pair."""
        query = "What is machine learning?"
        text = "Machine learning is a subset of artificial intelligence."
        
        score = reranker._score_single(query, text)
        
        # Should return a score between 0 and 1
        assert 0 <= score <= 1
        assert isinstance(score, float)
    
    def test_score_batch(self, reranker):
        """Test batch scoring."""
        query = "neural networks"
        texts = [
            "Neural networks are computing systems inspired by biological neural networks.",
            "Deep learning uses multi-layer neural networks.",
            "Traditional algorithms differ from neural approaches."
        ]
        
        scores = reranker.score_batch(query, texts)
        
        # Should return scores for all texts
        assert len(scores) == len(texts)
        assert all(0 <= score <= 1 for score in scores)
    
    @pytest.mark.asyncio
    async def test_score_batch_async(self, reranker):
        """Test async batch scoring."""
        query = "machine learning"
        texts = ["Text 1", "Text 2", "Text 3"]
        
        # Mock the synchronous score_batch method
        reranker.score_batch = Mock(return_value=[0.8, 0.6, 0.7])
        
        scores = await reranker.score_batch_async(query, texts)
        
        assert len(scores) == 3
        assert scores == [0.8, 0.6, 0.7]
    
    def test_caching(self, reranker):
        """Test that results are cached."""
        query = "test query"
        text = "test text"
        
        # First call
        score1 = reranker._cached_score(query, text)
        
        # Mock the model to return different score
        reranker.model.return_value.logits = torch.tensor([[0.1, 0.9]])
        
        # Second call should return cached result
        score2 = reranker._cached_score(query, text)
        
        assert score1 == score2  # Should be the same due to caching


class TestRerankingService:
    """Test suite for the reranking service."""
    
    @pytest.fixture
    def mock_cross_encoder(self):
        """Create a mock cross-encoder."""
        encoder = Mock(spec=CrossEncoderReranker)
        encoder.score_batch_async = AsyncMock(return_value=[0.9, 0.7, 0.5])
        return encoder
    
    @pytest.fixture
    def reranking_service(self, mock_cross_encoder):
        """Create a reranking service with mocked cross-encoder."""
        with patch('app.services.reranking_service.CrossEncoderReranker') as mock_class:
            mock_class.return_value = mock_cross_encoder
            service = RerankingService(
                cross_encoder_model='ms-marco-MiniLM',
                rerank_weight=0.6,
                original_weight=0.4
            )
            service.cross_encoder = mock_cross_encoder
            return service
    
    @pytest.mark.asyncio
    async def test_rerank_results(self, reranking_service):
        """Test reranking search results."""
        query = "neural network architectures"
        results = [
            {
                'paper_id': 'paper1',
                'chunk_id': 'chunk1',
                'chunk_text': 'Transformer architectures revolutionized NLP',
                'score': 0.8,
                'metadata': {
                    'title': 'Attention is All You Need',
                    'abstract': 'We propose a new architecture...'
                }
            },
            {
                'paper_id': 'paper2',
                'chunk_id': 'chunk2',
                'chunk_text': 'CNNs are effective for image processing',
                'score': 0.7,
                'metadata': {
                    'title': 'Deep Convolutional Networks',
                    'abstract': 'Convolutional neural networks...'
                }
            },
            {
                'paper_id': 'paper3',
                'chunk_id': 'chunk3',
                'chunk_text': 'RNNs handle sequential data well',
                'score': 0.6,
                'metadata': {
                    'title': 'Recurrent Neural Networks',
                    'abstract': 'For sequential data processing...'
                }
            }
        ]
        
        reranked = await reranking_service.rerank_results(query, results)
        
        # Verify results
        assert len(reranked) == 3
        assert all(isinstance(r, RerankingResult) for r in reranked)
        
        # Check that results are sorted by final score
        final_scores = [r.final_score for r in reranked]
        assert final_scores == sorted(final_scores, reverse=True)
        
        # Verify score calculation
        for i, result in enumerate(reranked):
            assert result.rerank_score == [0.9, 0.7, 0.5][i]
            assert 0 <= result.final_score <= 1
    
    @pytest.mark.asyncio
    async def test_rerank_with_context(self, reranking_service):
        """Test reranking with query context."""
        query = "transformer models"
        results = [
            {
                'paper_id': 'paper1',
                'chunk_id': 'chunk1',
                'chunk_text': 'Transformers use self-attention',
                'score': 0.8,
                'metadata': {}
            }
        ]
        
        query_context = {
            'previous': 'We need to improve our NLP model.',
            'current': 'Consider using transformer models.',
            'next': 'They have shown great results.'
        }
        
        # Mock context scoring
        reranking_service.cross_encoder.score_batch_async = AsyncMock(
            side_effect=[[0.9], [0.85]]  # First for main query, second for context
        )
        
        reranked = await reranking_service.rerank_results(
            query, results, query_context=query_context
        )
        
        # Should have context match score
        assert reranked[0].context_match is not None
        assert reranked[0].context_match > 0
    
    @pytest.mark.asyncio
    async def test_rerank_empty_results(self, reranking_service):
        """Test reranking with empty results."""
        reranked = await reranking_service.rerank_results("query", [])
        assert reranked == []
    
    @pytest.mark.asyncio
    async def test_rerank_top_k(self, reranking_service):
        """Test reranking with top_k limit."""
        query = "test query"
        results = [
            {
                'paper_id': f'paper{i}',
                'chunk_id': f'chunk{i}',
                'chunk_text': f'Text {i}',
                'score': 0.5,
                'metadata': {}
            }
            for i in range(10)
        ]
        
        # Mock scores
        reranking_service.cross_encoder.score_batch_async = AsyncMock(
            return_value=[0.9 - i*0.05 for i in range(10)]
        )
        
        reranked = await reranking_service.rerank_results(
            query, results, top_k=5
        )
        
        # Should only return top 5
        assert len(reranked) == 5
        
        # Should be the highest scoring ones
        assert all(r.rerank_score >= 0.65 for r in reranked)
    
    def test_weight_updates(self, reranking_service):
        """Test updating reranking weights."""
        reranking_service.update_weights(
            rerank_weight=0.8,
            original_weight=0.2,
            context_weight=0.1
        )
        
        assert reranking_service.rerank_weight == 0.8
        assert reranking_service.original_weight == 0.2
        assert reranking_service.context_weight == 0.1
        
        # Original weights should be normalized
        total = reranking_service.rerank_weight + reranking_service.original_weight
        assert abs(total - 1.0) < 0.001


class TestRerankingResult:
    """Test RerankingResult dataclass."""
    
    def test_reranking_result_creation(self):
        """Test creating a RerankingResult."""
        result = RerankingResult(
            paper_id="paper123",
            chunk_id="chunk456",
            chunk_text="Sample chunk text",
            original_score=0.75,
            rerank_score=0.85,
            final_score=0.82,
            metadata={"title": "Test Paper"},
            context_match=0.7
        )
        
        assert result.paper_id == "paper123"
        assert result.chunk_id == "chunk456"
        assert result.original_score == 0.75
        assert result.rerank_score == 0.85
        assert result.final_score == 0.82
        assert result.context_match == 0.7
        assert result.metadata["title"] == "Test Paper"