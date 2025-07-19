#!/usr/bin/env python3
"""Test search functionality directly."""
import asyncio
from app.db.session import AsyncSessionLocal
from app.services.citation_engine_v2 import EnhancedCitationEngine
from app.services.text_analysis import TextContext

async def test_search():
    """Test the search functionality."""
    async with AsyncSessionLocal() as db:
        engine = EnhancedCitationEngine(db)
        
        # Create a test context
        context = TextContext(
            current_sentence="Machine learning models have shown remarkable progress in natural language processing.",
            previous_sentence=None,
            next_sentence=None,
            paragraph="Machine learning models have shown remarkable progress in natural language processing.",
            position=0
        )
        
        print("Testing enhanced citation search...")
        
        # Test with different strategies
        for strategy in ["vector", "hybrid", "bm25"]:
            print(f"\n--- Testing {strategy} search ---")
            try:
                results = await engine.get_suggestions_enhanced(
                    text="Machine learning models have shown remarkable progress in natural language processing.",
                    context=context,
                    user_id="test-user",
                    use_reranking=False,  # Start without reranking
                    search_strategy=strategy
                )
                
                print(f"Got {len(results)} results")
                for i, result in enumerate(results[:3]):
                    print(f"\n{i+1}. {result.title}")
                    print(f"   Score: {result.confidence:.3f}")
                    print(f"   Chunk: {result.chunk_text[:100]}...")
                    
            except Exception as e:
                print(f"Error with {strategy}: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search())