#!/usr/bin/env python3
"""Debug WebSocket connection issues"""

import asyncio
import websockets
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_websocket_connection():
    """Test WebSocket connection and debug readyState issues"""
    
    # Test parameters
    user_id = "test-user-123"
    ws_url = f"ws://localhost:8000/ws/citations/v2?user_id={user_id}&use_enhanced=true&use_reranking=true&search_strategy=hybrid"
    
    print(f"\n{'='*60}")
    print(f"WebSocket Connection Debug Test")
    print(f"Time: {datetime.now()}")
    print(f"URL: {ws_url}")
    print(f"{'='*60}\n")
    
    try:
        # Attempt to connect
        print("1. Attempting to connect...")
        async with websockets.connect(ws_url) as websocket:
            print(f"✓ Connected! State: {websocket.state}")
            print(f"  - Local address: {websocket.local_address}")
            print(f"  - Remote address: {websocket.remote_address}")
            
            # Send a ping
            print("\n2. Sending ping message...")
            await websocket.send(json.dumps({"type": "ping"}))
            print("✓ Ping sent")
            
            # Wait for pong
            print("\n3. Waiting for pong response...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"✓ Received response: {data}")
            except asyncio.TimeoutError:
                print("✗ No response received within 5 seconds")
            
            # Test suggestion request
            print("\n4. Testing citation suggestion request...")
            test_message = {
                "type": "suggest",
                "text": "Machine learning has revolutionized many fields including natural language processing.",
                "context": {
                    "currentSentence": "Machine learning has revolutionized many fields including natural language processing.",
                    "cursorPosition": 85
                }
            }
            
            await websocket.send(json.dumps(test_message))
            print("✓ Suggestion request sent")
            
            # Wait for suggestions
            print("\n5. Waiting for suggestions...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(response)
                print(f"✓ Received {data.get('type', 'unknown')} response")
                if data.get('type') == 'suggestions':
                    print(f"  - Number of suggestions: {len(data.get('results', []))}")
                elif data.get('type') == 'error':
                    print(f"  - Error: {data.get('message', 'Unknown error')}")
            except asyncio.TimeoutError:
                print("✗ No response received within 10 seconds")
            
            # Check connection state
            print(f"\n6. Final connection state: {websocket.state}")
            
    except websockets.exceptions.WebSocketException as e:
        print(f"\n✗ WebSocket Error: {type(e).__name__}: {e}")
    except ConnectionRefusedError:
        print("\n✗ Connection refused - is the backend server running on port 8000?")
    except Exception as e:
        print(f"\n✗ Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

async def test_multiple_connections():
    """Test multiple simultaneous connections"""
    print(f"\n{'='*60}")
    print("Testing Multiple Simultaneous Connections")
    print(f"{'='*60}\n")
    
    connections = []
    for i in range(3):
        user_id = f"test-user-{i}"
        ws_url = f"ws://localhost:8000/ws/citations/v2?user_id={user_id}&use_enhanced=true"
        
        try:
            ws = await websockets.connect(ws_url)
            connections.append((user_id, ws))
            print(f"✓ Connected user {user_id}, state: {ws.state}")
        except Exception as e:
            print(f"✗ Failed to connect user {user_id}: {e}")
    
    # Send messages from all connections
    for user_id, ws in connections:
        try:
            await ws.send(json.dumps({"type": "ping"}))
            print(f"  - Sent ping from {user_id}")
        except Exception as e:
            print(f"  - Error sending from {user_id}: {e}")
    
    # Close all connections
    for user_id, ws in connections:
        await ws.close()
        print(f"  - Closed connection for {user_id}")

async def monitor_connection_state():
    """Monitor connection state changes over time"""
    print(f"\n{'='*60}")
    print("Monitoring Connection State Changes")
    print(f"{'='*60}\n")
    
    user_id = "monitor-user"
    ws_url = f"ws://localhost:8000/ws/citations/v2?user_id={user_id}"
    
    try:
        ws = await websockets.connect(ws_url)
        print(f"Initial state: {ws.state}")
        
        # Monitor for 15 seconds
        for i in range(15):
            await asyncio.sleep(1)
            print(f"  {i+1}s: State={ws.state}, Open={ws.open}, Closed={ws.closed}")
            
            # Send periodic pings
            if i % 5 == 0 and ws.open:
                try:
                    await ws.send(json.dumps({"type": "ping"}))
                    print(f"     → Sent ping")
                except Exception as e:
                    print(f"     → Error sending ping: {e}")
        
        await ws.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("WebSocket Connection Debugger")
    print("=============================\n")
    
    # Run tests
    asyncio.run(test_websocket_connection())
    asyncio.run(test_multiple_connections())
    asyncio.run(monitor_connection_state())
    
    print("\n✓ All tests completed")