"""Simple script to test WebSocket citation endpoint."""
import asyncio
import websockets
import json
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

async def test_websocket():
    """Test the WebSocket citation endpoint."""
    uri = "ws://localhost:8000/ws/citations?user_id=test-user"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {uri}")
            
            # Test 1: Send a ping
            await websocket.send(json.dumps({"type": "ping"}))
            response = await websocket.recv()
            print(f"Ping response: {response}")
            
            # Test 2: Send a suggestion request
            test_message = {
                "type": "suggest",
                "text": "Deep learning has revolutionized natural language processing with transformer architectures",
                "context": {
                    "currentSentence": "Deep learning has revolutionized natural language processing with transformer architectures",
                    "paragraph": "Deep learning has revolutionized natural language processing with transformer architectures. These models have achieved state-of-the-art results.",
                    "cursorPosition": 88
                }
            }
            
            print("\nSending suggestion request...")
            await websocket.send(json.dumps(test_message))
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            
            if data["type"] == "suggestions":
                print(f"\nReceived {len(data['results'])} suggestions:")
                for i, suggestion in enumerate(data['results'][:5]):
                    print(f"\n{i+1}. {suggestion['title']}")
                    print(f"   Authors: {', '.join(suggestion['authors'][:2])}...")
                    print(f"   Year: {suggestion['year']}")
                    print(f"   Confidence: {suggestion['confidence']:.3f}")
                    print(f"   Display: {suggestion['displayText']}")
            else:
                print(f"Unexpected response type: {data['type']}")
                print(f"Response: {data}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing WebSocket citation endpoint...")
    print("Make sure the backend is running on http://localhost:8000")
    print("-" * 50)
    asyncio.run(test_websocket())