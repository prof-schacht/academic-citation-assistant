#!/usr/bin/env python3
"""
Test script to verify the citation system is working properly.
"""
import asyncio
import json
from websockets import connect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_citation_system():
    """Test the citation system by sending a sample query."""
    # Test enhanced citations with hybrid search
    uri = "ws://localhost:8000/ws/citations/v2?user_id=test-user&use_enhanced=true&use_reranking=true&search_strategy=hybrid"
    
    try:
        async with connect(uri) as websocket:
            logger.info("Connected to WebSocket")
            
            # Send a test citation request
            test_message = {
                "type": "suggest",
                "text": "Recent advances in natural language processing have shown that transformer-based models like BERT and GPT have revolutionized the field. These models use self-attention mechanisms to capture long-range dependencies in text.",
                "context": {
                    "cursor_position": 100,
                    "document_id": "test-doc",
                    "section": "introduction"
                }
            }
            
            await websocket.send(json.dumps(test_message))
            logger.info("Sent test message")
            
            # Wait for response (might get pong first)
            suggestions_received = False
            for _ in range(3):  # Try up to 3 messages
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(response)
                
                if data.get("type") == "pong":
                    logger.info("Received pong (keepalive)")
                    continue
                elif data.get("type") == "suggestions":
                    suggestions_received = True
                    break
            
            if suggestions_received and data.get("type") == "suggestions":
                logger.info(f"Received {len(data.get('results', []))} suggestions")
                for i, result in enumerate(data.get('results', [])[:3]):
                    logger.info(f"\nSuggestion {i+1}:")
                    logger.info(f"  Title: {result.get('title')}")
                    logger.info(f"  Authors: {', '.join(result.get('authors', [])[:3])}")
                    logger.info(f"  Year: {result.get('year')}")
                    logger.info(f"  Confidence: {result.get('confidence'):.2f}")
            elif data.get("type") == "error":
                logger.error(f"Error: {data.get('message')}")
            else:
                logger.warning(f"Unexpected response type: {data.get('type')}")
                logger.info(f"Full response: {json.dumps(data, indent=2)}")
            
    except asyncio.TimeoutError:
        logger.error("Timeout waiting for response")
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_citation_system())