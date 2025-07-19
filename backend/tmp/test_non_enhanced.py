"""Test WebSocket with non-enhanced mode"""
import asyncio
import websockets
import json

async def test_non_enhanced():
    uri = "ws://localhost:8000/ws/citations/v2?user_id=test-user&use_enhanced=false&use_reranking=false&search_strategy=hybrid"
    
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")
        
        # Test citation suggestion
        suggestion_request = {
            "type": "suggest",
            "text": "Machine learning has revolutionized many fields including",
            "context": {
                "currentSentence": "Machine learning has revolutionized many fields including",
                "previousSentences": [],
                "nextSentences": [],
                "cursorPosition": 57
            }
        }
        
        await websocket.send(json.dumps(suggestion_request))
        print("Sent suggestion request")
        
        # Wait for response
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            response_data = json.loads(response)
            print(f"Received response: {json.dumps(response_data, indent=2)}")
            
            if response_data.get("type") == "suggestions":
                print(f"Got {len(response_data.get('suggestions', []))} suggestions")
                for i, sugg in enumerate(response_data.get('suggestions', [])[:3]):
                    print(f"  {i+1}. {sugg.get('title', 'No title')} ({sugg.get('year', 'No year')})")
        except asyncio.TimeoutError:
            print("Timeout waiting for suggestions")

if __name__ == "__main__":
    asyncio.run(test_non_enhanced())