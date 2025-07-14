"""Test script to verify the full system integration."""
import subprocess
import time
import sys
import os
import asyncio
import websockets
import json

def run_backend():
    """Start the backend server."""
    print("Starting backend server...")
    backend_process = subprocess.Popen(
        ["python", "run.py"],
        cwd=os.path.join(os.path.dirname(__file__), ".."),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for backend to start
    time.sleep(5)
    
    # Check if backend is running
    try:
        import requests
        response = requests.get("http://localhost:8000/api/health")
        if response.status_code == 200:
            print("✓ Backend is running")
            return backend_process
        else:
            print("✗ Backend health check failed")
            backend_process.terminate()
            return None
    except Exception as e:
        print(f"✗ Backend failed to start: {e}")
        backend_process.terminate()
        return None

async def test_websocket():
    """Test WebSocket connection."""
    print("\nTesting WebSocket connection...")
    try:
        uri = "ws://localhost:8000/ws/citations?user_id=test-user"
        async with websockets.connect(uri) as websocket:
            print("✓ WebSocket connected")
            
            # Send ping
            await websocket.send(json.dumps({"type": "ping"}))
            response = await websocket.recv()
            data = json.loads(response)
            if data.get("type") == "pong":
                print("✓ WebSocket ping/pong working")
            
            # Send test query
            test_message = {
                "type": "suggest",
                "text": "I'm researching transformer architectures for natural language processing",
                "context": {
                    "currentSentence": "I'm researching transformer architectures for natural language processing",
                    "paragraph": "I'm researching transformer architectures for natural language processing.",
                    "cursorPosition": 70
                }
            }
            
            await websocket.send(json.dumps(test_message))
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get("type") == "suggestions" and data.get("results"):
                print(f"✓ Received {len(data['results'])} suggestions")
                print("\nTop 3 suggestions:")
                for i, suggestion in enumerate(data['results'][:3]):
                    print(f"  {i+1}. {suggestion['title']} (confidence: {suggestion['confidence']:.3f})")
            else:
                print("✗ No suggestions received")
                
    except Exception as e:
        print(f"✗ WebSocket test failed: {e}")

def check_test_data():
    """Check if test data exists in database."""
    print("\nChecking test data...")
    try:
        from sqlalchemy import create_engine, text
        from app.core.config import settings
        
        # Use sync engine for simple check
        engine = create_engine(settings.database_url.replace("+asyncpg", ""))
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM papers WHERE embedding IS NOT NULL"))
            count = result.scalar()
            
            if count > 0:
                print(f"✓ Found {count} papers with embeddings")
                return True
            else:
                print("✗ No papers with embeddings found")
                print("  Run: python scripts/populate_test_papers_v2.py")
                return False
    except Exception as e:
        print(f"✗ Database check failed: {e}")
        return False

def main():
    """Run full system test."""
    print("=== Academic Citation Assistant System Test ===\n")
    
    # Add backend to path
    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    
    # Check test data
    if not check_test_data():
        print("\nPlease populate test data first!")
        return
    
    # Start backend
    backend_process = run_backend()
    if not backend_process:
        return
    
    try:
        # Test WebSocket
        asyncio.run(test_websocket())
        
        print("\n=== Frontend Integration ===")
        print("\nTo test the full system:")
        print("1. Keep this backend running")
        print("2. In another terminal: cd frontend && npm run dev")
        print("3. Open http://localhost:3000 in your browser")
        print("4. Create or open a document")
        print("5. Start typing about 'transformers', 'BERT', or 'deep learning'")
        print("6. Watch the citation panel on the right for real-time suggestions!")
        print("\nPress Ctrl+C to stop the backend...")
        
        # Keep backend running
        backend_process.wait()
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        backend_process.terminate()
        backend_process.wait()

if __name__ == "__main__":
    main()