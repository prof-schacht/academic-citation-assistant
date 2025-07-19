"""Debug suggestion processing issue"""
import asyncio
import websockets
import json
import time

async def debug_suggestion():
    uri = "ws://localhost:8000/ws/citations/v2?user_id=debug-user&use_enhanced=false&use_reranking=false&search_strategy=vector"
    
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")
        
        # Send multiple messages and track responses
        messages = [
            {
                "type": "ping"
            },
            {
                "type": "suggest",
                "text": "Machine learning has revolutionized many fields including natural language processing and computer vision",
                "context": {
                    "currentSentence": "Machine learning has revolutionized many fields including natural language processing and computer vision",
                    "previousSentences": [],
                    "nextSentences": [],
                    "cursorPosition": 100
                }
            }
        ]
        
        for msg in messages:
            print(f"\nSending message type: {msg['type']}")
            await websocket.send(json.dumps(msg))
            
            # Wait for responses with timeout
            start_time = time.time()
            responses_received = []
            
            while time.time() - start_time < 3.0:  # 3 second timeout
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                    response_data = json.loads(response)
                    responses_received.append(response_data)
                    print(f"  Received: {response_data.get('type', 'unknown')} - {json.dumps(response_data)[:100]}...")
                    
                    # Break if we get suggestions
                    if response_data.get('type') == 'suggestions':
                        break
                except asyncio.TimeoutError:
                    continue
            
            if not responses_received:
                print("  No response received")
            
            await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(debug_suggestion())