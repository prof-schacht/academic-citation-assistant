#!/usr/bin/env python
"""Test WebSocket citation suggestions directly."""
import asyncio
import json
import websockets

async def test_websocket():
    uri = "ws://localhost:8000/ws/citations?user_id=test-user"
    
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")
        
        # Send a test query
        test_message = {
            "type": "suggest",
            "text": "Transformers are neural network architectures that have revolutionized natural language processing",
            "context": {
                "currentSentence": "Transformers are neural network architectures that have revolutionized natural language processing",
                "paragraph": "Transformers are neural network architectures that have revolutionized natural language processing.",
                "cursorPosition": 95
            }
        }
        
        await websocket.send(json.dumps(test_message))
        print("Sent test message")
        
        # Wait for response
        response = await websocket.recv()
        data = json.loads(response)
        
        print(f"\nReceived response type: {data.get('type')}")
        
        if data.get('type') == 'suggestions' and data.get('results'):
            print(f"Got {len(data['results'])} suggestions:")
            for i, suggestion in enumerate(data['results'][:3]):
                print(f"\n{i+1}. {suggestion['title']}")
                print(f"   Authors: {', '.join(suggestion['authors'][:3])}...")
                print(f"   Year: {suggestion['year']}")
                print(f"   Confidence: {suggestion['confidence']:.3f}")
        else:
            print("Response:", data)

if __name__ == "__main__":
    asyncio.run(test_websocket())