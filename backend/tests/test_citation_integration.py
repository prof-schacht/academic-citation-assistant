"""Integration test for citation system with real data."""
import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import numpy as np

from app.db.session import engine
from app.models.paper import Paper
from app.services.citation_engine import CitationEngine
from app.services.text_analysis import TextContext
from app.services.vector_search_v2 import VectorSearchService, SearchOptions
from app.services.embedding import EmbeddingService


@pytest.mark.asyncio
async def test_citation_engine_with_real_data():
    """Test citation engine with papers in the database."""
    async with AsyncSession(engine) as session:
        # Check if we have papers
        result = await session.execute(select(Paper).limit(1))
        papers = result.scalars().all()
        
        if not papers:
            pytest.skip("No papers in database. Run populate_test_papers_v2.py first.")
        
        # Initialize citation engine
        citation_engine = CitationEngine(session)
        
        # Create test context
        context = TextContext(
            current_sentence="I'm researching transformer architectures for natural language processing",
            previous_sentence="Deep learning has made significant advances recently.",
            paragraph="Deep learning has made significant advances recently. I'm researching transformer architectures for natural language processing."
        )
        
        # Get suggestions - use lower threshold since test data might not have perfect matches
        suggestions = await citation_engine.get_suggestions(
            text="I'm researching transformer architectures for natural language processing",
            context=context,
            user_id="test-user",
            options=SearchOptions(limit=10, min_similarity=0.3)
        )
        
        # Verify we got suggestions
        assert len(suggestions) > 0
        
        # Check the top suggestion
        top_suggestion = suggestions[0]
        assert top_suggestion.title is not None
        assert top_suggestion.confidence > 0.5
        assert top_suggestion.display_text is not None
        
        # Print results for debugging
        print(f"\nFound {len(suggestions)} suggestions:")
        for i, suggestion in enumerate(suggestions[:3]):
            print(f"{i+1}. {suggestion.title}")
            print(f"   Confidence: {suggestion.confidence:.3f}")
            print(f"   Display: {suggestion.display_text}")


@pytest.mark.asyncio
async def test_vector_search_directly():
    """Test vector search service directly."""
    async with AsyncSession(engine) as session:
        # Initialize services
        embedding_service = EmbeddingService()
        vector_search = VectorSearchService(session)
        
        # Generate embedding for test query
        test_query = "How do transformers work in NLP?"
        embedding = await embedding_service.generate_embedding(test_query)
        
        # Search for similar papers
        results = await vector_search.search_similar_chunks(
            embedding=embedding,
            user_id="test-user",
            options=SearchOptions(limit=5, min_similarity=0.3)
        )
        
        # Verify results
        assert len(results) > 0
        
        # Check first result
        first_result = results[0]
        assert first_result.title is not None
        assert first_result.similarity > 0.3
        assert first_result.similarity <= 1.0
        
        # Print results for debugging
        print(f"\nVector search found {len(results)} results:")
        for i, result in enumerate(results):
            print(f"{i+1}. {result.title}")
            print(f"   Similarity: {result.similarity:.3f}")
            print(f"   Year: {result.year}")


@pytest.mark.asyncio
async def test_embedding_generation():
    """Test embedding generation."""
    embedding_service = EmbeddingService()
    
    # Test single embedding
    text = "Machine learning is transforming many industries"
    embedding = await embedding_service.generate_embedding(text)
    
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (384,)  # all-MiniLM-L6-v2 dimension
    assert embedding.dtype == np.float32
    
    # Test batch embeddings
    texts = [
        "Deep learning for NLP",
        "Computer vision with transformers",
        "Reinforcement learning algorithms"
    ]
    embeddings = await embedding_service.generate_batch_embeddings(texts)
    
    assert len(embeddings) == 3
    for emb in embeddings:
        assert isinstance(emb, np.ndarray)
        assert emb.shape == (384,)


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_citation_engine_with_real_data())
    asyncio.run(test_vector_search_directly())
    asyncio.run(test_embedding_generation())