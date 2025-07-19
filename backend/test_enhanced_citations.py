"""
Test script to debug enhanced citation issues
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.citation_engine_v2 import EnhancedCitationEngine
from app.services.text_analysis import TextContext
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_enhanced_citations():
    """Test the enhanced citation engine"""
    
    # Create database connection
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Initialize enhanced citation engine
        print("Initializing EnhancedCitationEngine...")
        citation_engine = EnhancedCitationEngine(session)
        
        # Create test context
        context = TextContext(
            current_sentence="Machine learning models have shown remarkable performance in various tasks.",
            previous_sentence="Recent advances in AI have been significant.",
            next_sentence="These models can be applied to many domains.",
            section="Introduction",
            surrounding_text="Recent advances in AI have been significant. Machine learning models have shown remarkable performance in various tasks. These models can be applied to many domains."
        )
        
        # Test with enhanced features disabled
        print("\n1. Testing with enhanced features DISABLED...")
        try:
            suggestions = await citation_engine.get_suggestions_enhanced(
                text=context.current_sentence,
                context=context,
                user_id="test_user",
                use_reranking=False,
                search_strategy="vector"
            )
            print(f"Got {len(suggestions)} suggestions with vector search only")
            for i, s in enumerate(suggestions[:3]):
                print(f"  {i+1}. {s.title} ({s.year}) - confidence: {s.confidence:.3f}")
        except Exception as e:
            print(f"Error with vector search: {e}")
            import traceback
            traceback.print_exc()
        
        # Test with hybrid search only
        print("\n2. Testing with hybrid search (no reranking)...")
        try:
            suggestions = await citation_engine.get_suggestions_enhanced(
                text=context.current_sentence,
                context=context,
                user_id="test_user",
                use_reranking=False,
                search_strategy="hybrid"
            )
            print(f"Got {len(suggestions)} suggestions with hybrid search")
            for i, s in enumerate(suggestions[:3]):
                print(f"  {i+1}. {s.title} ({s.year}) - confidence: {s.confidence:.3f}")
        except Exception as e:
            print(f"Error with hybrid search: {e}")
            import traceback
            traceback.print_exc()
        
        # Test with full enhanced features
        print("\n3. Testing with FULL enhanced features (hybrid + reranking)...")
        try:
            suggestions = await citation_engine.get_suggestions_enhanced(
                text=context.current_sentence,
                context=context,
                user_id="test_user",
                use_reranking=True,
                search_strategy="hybrid"
            )
            print(f"Got {len(suggestions)} suggestions with full enhanced features")
            for i, s in enumerate(suggestions[:3]):
                print(f"  {i+1}. {s.title} ({s.year}) - confidence: {s.confidence:.3f}")
                print(f"     Scores - BM25: {s.bm25_score:.3f}, Rerank: {s.rerank_score:.3f}, Hybrid: {s.hybrid_score:.3f}")
        except Exception as e:
            print(f"Error with full enhanced features: {e}")
            import traceback
            traceback.print_exc()
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_enhanced_citations())