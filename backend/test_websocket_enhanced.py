"""
Test WebSocket v2 endpoint with enhanced features
"""
import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_websocket_enhanced():
    """Test WebSocket v2 with enhanced features"""
    
    # Test different configurations
    test_configs = [
        {
            "name": "Vector Search Only",
            "params": "use_enhanced=false&use_reranking=false&search_strategy=vector",
            "expected_features": {"use_enhanced": False, "use_reranking": False}
        },
        {
            "name": "Hybrid Search (No Reranking)",
            "params": "use_enhanced=true&use_reranking=false&search_strategy=hybrid",
            "expected_features": {"use_enhanced": True, "use_reranking": False}
        },
        {
            "name": "Full Enhanced (Hybrid + Reranking)",
            "params": "use_enhanced=true&use_reranking=true&search_strategy=hybrid",
            "expected_features": {"use_enhanced": True, "use_reranking": True}
        }
    ]
    
    for config in test_configs:
        print(f"\n{'='*60}")
        print(f"Testing: {config['name']}")
        print(f"Parameters: {config['params']}")
        print('='*60)
        
        uri = f"ws://localhost:8000/api/v2/ws/citations?user_id=test_user&{config['params']}"
        
        try:
            async with websockets.connect(uri) as websocket:
                # Send a test query
                test_message = {
                    "type": "suggest",
                    "text": "Recent advances in machine learning have shown that transformer architectures can achieve state-of-the-art performance on various natural language processing tasks.",
                    "context": {
                        "section": "Introduction",
                        "paragraph": "The field of artificial intelligence has seen remarkable progress in recent years. Recent advances in machine learning have shown that transformer architectures can achieve state-of-the-art performance on various natural language processing tasks. These models have revolutionized how we approach text understanding."
                    }
                }
                
                await websocket.send(json.dumps(test_message))
                print(f"Sent test message, waiting for response...")
                
                # Wait for response with timeout
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    data = json.loads(response)
                    
                    if data.get("type") == "suggestions":
                        results = data.get("results", [])
                        print(f"\nReceived {len(results)} suggestions")
                        print(f"Search strategy used: {data.get('searchStrategy', 'unknown')}")
                        print(f"Reranking used: {data.get('usedReranking', False)}")
                        
                        # Show top 3 results
                        for i, result in enumerate(results[:3]):
                            print(f"\n{i+1}. {result['title']} ({result['year']})")
                            print(f"   Confidence: {result['confidence']:.3f}")
                            if 'scores' in result:
                                scores = result['scores']
                                print(f"   Scores - Hybrid: {scores.get('hybrid', 0):.3f}, "
                                      f"BM25: {scores.get('bm25', 0):.3f}, "
                                      f"Rerank: {scores.get('rerank', 0):.3f}")
                    else:
                        print(f"Unexpected response type: {data.get('type')}")
                        print(f"Response: {json.dumps(data, indent=2)}")
                        
                except asyncio.TimeoutError:
                    print("ERROR: Request timed out after 30 seconds")
                    
        except Exception as e:
            print(f"ERROR: Failed to connect or process: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("Testing WebSocket v2 endpoint with enhanced features...")
    asyncio.run(test_websocket_enhanced())