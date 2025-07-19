#!/usr/bin/env python3
"""Test WebSocket connection and citation suggestions."""
import asyncio
import json
import websockets

async def test_websocket():
    """Test the WebSocket connection."""
    # Test both v1 and v2 endpoints
    endpoints = [
        "ws://localhost:8000/ws/citations?user_id=test-user",
        "ws://localhost:8000/ws/citations/v2?user_id=test-user&use_enhanced=true&search_strategy=hybrid"
    ]
    
    test_text = "Machine learning models have shown remarkable progress in natural language processing tasks."
    
    for endpoint in endpoints:
        print(f"\nTesting endpoint: {endpoint}")
        try:
            async with websockets.connect(endpoint) as websocket:
                print("Connected successfully")
                
                # Send a test message
                message = {
                    "type": "suggest",
                    "text": test_text,
                    "context": {
                        "cursorPosition": len(test_text),
                        "section": "introduction"
                    }
                }
                
                await websocket.send(json.dumps(message))
                print(f"Sent message: {message}")
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    result = json.loads(response)
                    print(f"Received response: {json.dumps(result, indent=2)}")
                    
                    if result.get("type") == "suggestions":
                        print(f"Got {len(result.get('results', []))} suggestions")
                    elif result.get("type") == "error":
                        print(f"Error: {result.get('message')}")
                except asyncio.TimeoutError:
                    print("No response received within 5 seconds")
                    
        except Exception as e:
            print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())