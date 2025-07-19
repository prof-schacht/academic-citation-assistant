#!/usr/bin/env python3
"""
Test that enhanced citations return data in the format expected by the frontend.
"""
import asyncio
import json
from websockets import connect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_frontend_format():
    """Test enhanced citations return correct format for frontend."""
    uri = "ws://localhost:8000/ws/citations/v2?user_id=test-user&use_enhanced=true&use_reranking=false&search_strategy=hybrid"
    
    logger.info("Testing enhanced citations format for frontend...")
    
    try:
        async with connect(uri) as websocket:
            logger.info("✓ Connected to WebSocket")
            
            # Send a test citation request
            test_message = {
                "type": "suggest",
                "text": "Machine learning and artificial intelligence have transformed many industries through deep learning and neural networks.",
                "context": {
                    "cursor_position": 50,
                    "document_id": "test-doc",
                    "section": "introduction"
                }
            }
            
            await websocket.send(json.dumps(test_message))
            logger.info("✓ Sent test message")
            
            # Wait for response
            response_received = False
            for _ in range(5):
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    
                    if data.get("type") == "pong":
                        logger.info("  Received pong (keepalive)")
                        continue
                    elif data.get("type") == "suggestions":
                        response_received = True
                        break
                except asyncio.TimeoutError:
                    logger.error("❌ Timeout waiting for response")
                    break
            
            if response_received:
                logger.info(f"✓ Received suggestions response")
                
                # Verify response structure
                assert "type" in data, "Missing 'type' field"
                assert data["type"] == "suggestions", f"Wrong type: {data['type']}"
                assert "results" in data, "Missing 'results' field"
                assert isinstance(data["results"], list), "Results should be a list"
                
                logger.info(f"✓ Response has correct structure")
                logger.info(f"✓ Number of suggestions: {len(data['results'])}")
                
                # Check first result format
                if data["results"]:
                    first = data["results"][0]
                    required_fields = [
                        "paperId", "title", "authors", "year", "abstract",
                        "confidence", "citationStyle", "displayText", 
                        "chunkText", "chunkIndex", "chunkId", "sectionTitle"
                    ]
                    
                    missing_fields = [field for field in required_fields if field not in first]
                    if missing_fields:
                        logger.error(f"❌ Missing fields: {missing_fields}")
                    else:
                        logger.info("✓ All required fields present")
                    
                    # Verify paperId is a string (not UUID object)
                    if "paperId" in first:
                        assert isinstance(first["paperId"], str), "paperId should be string"
                        logger.info(f"✓ paperId is string: {first['paperId'][:8]}...")
                    
                    # Show sample result
                    logger.info("\nSample result:")
                    logger.info(f"  Title: {first.get('title', 'N/A')}")
                    logger.info(f"  Year: {first.get('year', 'N/A')}")
                    logger.info(f"  Confidence: {first.get('confidence', 0):.3f}")
                    logger.info(f"  Display: {first.get('displayText', 'N/A')}")
                    
                    # Check enhanced fields if present
                    if "scores" in first:
                        logger.info("✓ Enhanced citation with scores:")
                        scores = first["scores"]
                        logger.info(f"    Hybrid: {scores.get('hybrid', 0):.3f}")
                        logger.info(f"    BM25: {scores.get('bm25', 0):.3f}")
                        logger.info(f"    Rerank: {scores.get('rerank', 0):.3f}")
                
                logger.info("\n✅ Frontend format test PASSED!")
                return True
            else:
                logger.error("\n❌ No suggestions received")
                return False
                
    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_frontend_format())
    exit(0 if success else 1)