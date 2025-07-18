"""Tests for the advanced chunking service."""
import pytest
from app.services.advanced_chunking import (
    AdvancedChunkingService,
    ChunkingStrategy,
    EnhancedTextChunk
)


class TestAdvancedChunking:
    """Test suite for advanced chunking functionality."""
    
    @pytest.fixture
    def chunking_service(self):
        """Create a chunking service instance."""
        return AdvancedChunkingService(
            chunk_size=100,
            chunk_overlap=20,
            min_chunk_size=50,
            max_chunk_size=200
        )
    
    @pytest.fixture
    def sample_paper_text(self):
        """Sample academic paper text for testing."""
        return """
Abstract
This paper presents a novel approach to neural machine translation using transformer architectures. 
We demonstrate significant improvements over baseline models on multiple language pairs.

Introduction
Machine translation has been a fundamental challenge in natural language processing for decades. 
Recent advances in deep learning have revolutionized the field. 
Transformer models, introduced by Vaswani et al., have become the dominant architecture.

Methods
We propose a modified attention mechanism that incorporates linguistic features. 
Our approach differs from standard transformers in three key ways.
First, we use positional encodings that capture syntactic information.
Second, we introduce a hierarchical attention layer.
Third, we employ a novel training objective that combines multiple loss functions.

Results
Our experiments show consistent improvements across all tested language pairs.
On the WMT benchmark, we achieve a BLEU score of 45.2, outperforming the baseline by 3.1 points.
The improvements are particularly pronounced for morphologically rich languages.

Discussion
The results suggest that incorporating linguistic knowledge into neural architectures is beneficial.
However, there are limitations to our approach that warrant further investigation.
Future work should explore the scalability of these methods to larger datasets.

Conclusion
We have presented a linguistically-informed transformer model for machine translation.
The empirical results validate our hypothesis about the importance of syntactic features.
This work opens new avenues for combining neural and symbolic approaches in NLP.
"""
    
    def test_sentence_aware_chunking(self, chunking_service, sample_paper_text):
        """Test sentence-aware chunking strategy."""
        chunks = chunking_service.chunk_text(
            sample_paper_text,
            strategy=ChunkingStrategy.SENTENCE_AWARE
        )
        
        # Verify chunks are created
        assert len(chunks) > 0
        
        # Verify chunk properties
        for chunk in chunks:
            assert isinstance(chunk, EnhancedTextChunk)
            assert chunk.text
            assert chunk.word_count > 0
            assert chunk.sentence_count > 0
            assert chunk.chunk_index >= 0
            
        # Verify sentence boundaries are respected
        for chunk in chunks:
            # Check that chunks end with sentence-ending punctuation
            text = chunk.text.strip()
            if text:
                assert text[-1] in '.!?\n' or chunk == chunks[-1]
    
    def test_hierarchical_chunking(self, chunking_service, sample_paper_text):
        """Test hierarchical chunking with section detection."""
        chunks = chunking_service.chunk_text(
            sample_paper_text,
            strategy=ChunkingStrategy.HIERARCHICAL
        )
        
        # Verify sections are detected
        sections = set(chunk.section for chunk in chunks if chunk.section)
        expected_sections = {'abstract', 'intro', 'methods', 'results', 'discussion', 'conclusion'}
        
        # Check that at least some expected sections are found
        assert len(sections.intersection(expected_sections)) >= 4
        
        # Verify chunk types are set correctly
        for chunk in chunks:
            if chunk.section:
                assert chunk.chunk_type in ['abstract', 'intro', 'methods', 'results', 'discussion', 'conclusion', 'body']
    
    def test_element_based_chunking(self, chunking_service, sample_paper_text):
        """Test element-based chunking by paragraphs."""
        chunks = chunking_service.chunk_text(
            sample_paper_text,
            strategy=ChunkingStrategy.ELEMENT_BASED
        )
        
        # Verify chunks are created for each paragraph
        assert len(chunks) > 0
        
        # Count paragraphs in original text
        paragraphs = [p.strip() for p in sample_paper_text.strip().split('\n\n') if p.strip()]
        
        # Should have roughly the same number of chunks as paragraphs
        # (some might be split if too large)
        assert len(chunks) >= len(paragraphs) - 2  # Allow some flexibility
    
    def test_chunk_overlap(self, chunking_service):
        """Test that overlapping works correctly."""
        text = " ".join([f"Sentence {i}." for i in range(50)])
        
        chunks = chunking_service.chunk_text(
            text,
            strategy=ChunkingStrategy.SENTENCE_AWARE
        )
        
        # Check for overlap between consecutive chunks
        for i in range(len(chunks) - 1):
            chunk1_words = set(chunks[i].text.split()[-10:])  # Last 10 words
            chunk2_words = set(chunks[i+1].text.split()[:10])  # First 10 words
            
            # Should have some overlap
            overlap = chunk1_words.intersection(chunk2_words)
            assert len(overlap) > 0 or chunks[i].word_count < 20  # Small chunks might not overlap
    
    def test_metadata_preservation(self, chunking_service, sample_paper_text):
        """Test that metadata is preserved in chunks."""
        metadata = {
            'paper_id': '12345',
            'title': 'Test Paper',
            'authors': ['John Doe', 'Jane Smith']
        }
        
        chunks = chunking_service.chunk_text(
            sample_paper_text,
            strategy=ChunkingStrategy.SENTENCE_AWARE,
            metadata=metadata
        )
        
        # Verify metadata is preserved in all chunks
        for chunk in chunks:
            assert chunk.metadata == metadata
    
    def test_character_positions(self, chunking_service):
        """Test that character positions are calculated correctly."""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        
        chunks = chunking_service.chunk_text(
            text,
            strategy=ChunkingStrategy.SENTENCE_AWARE
        )
        
        # Verify character positions
        for chunk in chunks:
            # Extract text using character positions
            extracted = text[chunk.start_char:chunk.end_char]
            # Should match the chunk text (allowing for whitespace differences)
            assert extracted.strip() == chunk.text.strip()
    
    def test_small_text_handling(self, chunking_service):
        """Test handling of text smaller than chunk size."""
        small_text = "This is a very short text."
        
        chunks = chunking_service.chunk_text(
            small_text,
            strategy=ChunkingStrategy.SENTENCE_AWARE
        )
        
        # Should create exactly one chunk
        assert len(chunks) == 1
        assert chunks[0].text.strip() == small_text.strip()
    
    def test_merge_small_chunks(self, chunking_service):
        """Test merging of small chunks."""
        # Create some small chunks
        chunks = [
            EnhancedTextChunk(
                text=f"Chunk {i}",
                start_char=i*10,
                end_char=(i+1)*10,
                chunk_index=i,
                word_count=2,
                sentence_count=1
            )
            for i in range(5)
        ]
        
        merged = chunking_service.merge_small_chunks(chunks, min_size=5)
        
        # Should have fewer chunks after merging
        assert len(merged) < len(chunks)
        
        # Each merged chunk should have at least min_size words
        for chunk in merged[:-1]:  # Except possibly the last one
            assert chunk.word_count >= 5


class TestChunkingStrategies:
    """Test different chunking strategies with edge cases."""
    
    @pytest.fixture
    def service(self):
        return AdvancedChunkingService(chunk_size=50, chunk_overlap=10)
    
    def test_empty_text(self, service):
        """Test handling of empty text."""
        for strategy in ChunkingStrategy:
            chunks = service.chunk_text("", strategy=strategy)
            assert len(chunks) == 0
    
    def test_whitespace_only(self, service):
        """Test handling of whitespace-only text."""
        for strategy in ChunkingStrategy:
            chunks = service.chunk_text("   \n\n   \t   ", strategy=strategy)
            assert len(chunks) == 0 or all(not chunk.text.strip() for chunk in chunks)
    
    def test_single_word(self, service):
        """Test handling of single word text."""
        for strategy in ChunkingStrategy:
            chunks = service.chunk_text("Hello", strategy=strategy)
            assert len(chunks) == 1
            assert chunks[0].text.strip() == "Hello"
    
    def test_no_sentence_endings(self, service):
        """Test text without sentence endings."""
        text = "This is a long text without any sentence endings just continuous words " * 20
        
        chunks = service.chunk_text(text, strategy=ChunkingStrategy.SENTENCE_AWARE)
        
        # Should still create chunks even without sentence boundaries
        assert len(chunks) > 0
        
        # Verify chunks don't exceed max size
        for chunk in chunks:
            assert chunk.word_count <= service.max_chunk_size