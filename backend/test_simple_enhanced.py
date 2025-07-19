#!/usr/bin/env python3
"""
Simple test for enhanced citations with reranking.
"""
import asyncio
import json
from websockets import connect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_enhanced_with_reranking():
    """Test enhanced citations with reranking enabled."""
    uri = "ws://localhost:8000/ws/citations/v2?user_id=test-user&use_enhanced=true&use_reranking=true&search_strategy=hybrid"
    
    logger.info("Testing enhanced citations with reranking...")
    
    try:
        async with connect(uri) as websocket:
            logger.info("✅ Connected to WebSocket")
            
            # Send a test citation request
            test_message = {
                "type": "suggest",
                "text": "Large Language models which get's more and more capable are best attack models for machine learning applications.",
                "context": {
                    "currentSentence": "Large Language models which get's more and more capable are best attack models for machine learning applications.",
                    "previousSentence": "The theory of mind is important if models get more and more capable.",
                    "cursorPosition": 98,
                    "textLength": 115
                }
            }
            
            await websocket.send(json.dumps(test_message))
            logger.info("✅ Sent test message")
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                data = json.loads(response)
                
                if data.get("type") == "suggestions":
                    logger.info(f"✅ Received {len(data.get('results', []))} suggestions")
                    
                    # Show first result with scores
                    if data.get("results"):
                        first = data["results"][0]
                        logger.info(f"\nFirst result:")
                        logger.info(f"  Title: {first.get('title')}")
                        logger.info(f"  Confidence: {first.get('confidence')}")
                        
                        if "scores" in first:
                            scores = first["scores"]
                            logger.info(f"  Scores:")
                            logger.info(f"    Hybrid: {scores.get('hybrid')}")
                            logger.info(f"    BM25: {scores.get('bm25')}")
                            logger.info(f"    Rerank: {scores.get('rerank')}")
                    
                    return True
                elif data.get("type") == "error":
                    logger.error(f"❌ Error response: {data.get('message')}")
                    return False
                else:
                    logger.warning(f"⚠️ Unexpected response type: {data.get('type')}")
                    return False
                    
            except asyncio.TimeoutError:
                logger.error("❌ Timeout - no response received within 15 seconds")
                return False
                
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_enhanced_with_reranking())
    if success:
        logger.info("\n🎉 Enhanced citations with reranking are working!")
    else:
        logger.error("\n💥 Enhanced citations with reranking failed")
    exit(0 if success else 1)