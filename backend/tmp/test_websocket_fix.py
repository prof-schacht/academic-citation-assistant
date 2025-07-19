"""Test script to verify WebSocket JSON serialization fix."""
import asyncio
import websockets
import json

async def test_websocket_connection():
    """Test WebSocket connection after fixing Query parameter issue."""
    
    # Test URLs with query parameters
    test_urls = [
        "ws://localhost:8000/ws/citations?user_id=test-user",
        "ws://localhost:8000/ws/citations/v2?user_id=test-user&use_enhanced=true&use_reranking=true&search_strategy=hybrid",
        "ws://localhost:8000/ws/citations/v2?user_id=test-user&use_enhanced=false"
    ]
    
    for url in test_urls:
        print(f"\nTesting: {url}")
        try:
            async with websockets.connect(url) as websocket:
                print("✓ Connected successfully")
                
                # Send a test message
                test_message = {
                    "type": "suggest",
                    "text": "Recent advances in neural networks have shown significant improvements in natural language processing tasks.",
                    "context": {}
                }
                
                await websocket.send(json.dumps(test_message))
                print("✓ Sent test message")
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    result = json.loads(response)
                    print(f"✓ Received response: {result.get('type', 'unknown')}")
                    
                    if result.get('type') == 'error':
                        print(f"  Error: {result.get('message', 'Unknown error')}")
                    elif result.get('type') == 'suggestions':
                        print(f"  Suggestions count: {len(result.get('results', []))}")
                        print(f"  Search strategy: {result.get('searchStrategy', 'N/A')}")
                        print(f"  Used reranking: {result.get('usedReranking', False)}")
                        
                except asyncio.TimeoutError:
                    print("✗ No response received within 5 seconds")
                    
        except websockets.exceptions.WebSocketException as e:
            print(f"✗ WebSocket error: {e}")
        except Exception as e:
            print(f"✗ Unexpected error: {e}")

if __name__ == "__main__":
    print("Testing WebSocket endpoints after Query parameter fix...")
    print("Make sure the backend server is running on localhost:8000")
    asyncio.run(test_websocket_connection())