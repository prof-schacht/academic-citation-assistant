#!/usr/bin/env python3
"""
Measure actual performance of enhanced citations.
"""
import asyncio
import json
import time
from websockets import connect
import logging

logging.basicConfig(level=logging.WARNING)  # Reduce noise
logger = logging.getLogger(__name__)

async def measure_citation_performance():
    """Measure performance of different citation modes."""
    
    test_configs = [
        ("Vector Search", "ws://localhost:8000/ws/citations/v2?user_id=test-user&use_enhanced=true&use_reranking=false&search_strategy=vector"),
        ("Hybrid Search", "ws://localhost:8000/ws/citations/v2?user_id=test-user&use_enhanced=true&use_reranking=false&search_strategy=hybrid"),
        ("Hybrid + Reranking", "ws://localhost:8000/ws/citations/v2?user_id=test-user&use_enhanced=true&use_reranking=true&search_strategy=hybrid"),
    ]
    
    test_query = "Machine learning and deep learning models have revolutionized natural language processing and computer vision applications in recent years."
    
    for test_name, uri in test_configs:
        print(f"\n📊 Testing {test_name}:")
        times = []
        successes = 0
        
        for run in range(3):  # 3 runs per test
            try:
                start_time = time.time()
                
                async with connect(uri) as websocket:
                    test_message = {
                        "type": "suggest",
                        "text": test_query,
                        "context": {
                            "currentSentence": test_query,
                            "cursorPosition": 50,
                            "textLength": len(test_query)
                        }
                    }
                    
                    await websocket.send(json.dumps(test_message))
                    
                    # Wait for response with timeout
                    response = await asyncio.wait_for(websocket.recv(), timeout=20.0)
                    data = json.loads(response)
                    
                    if data.get("type") == "suggestions":
                        end_time = time.time()
                        duration = end_time - start_time
                        times.append(duration)
                        successes += 1
                        
                        result_count = len(data.get("results", []))
                        print(f"  Run {run+1}: {duration:.2f}s ({result_count} results)")
                        
                        # Show scoring info for first run
                        if run == 0 and data.get("results"):
                            first = data["results"][0]
                            if "scores" in first:
                                scores = first["scores"]
                                print(f"    Sample scores - Hybrid: {scores.get('hybrid', 0):.3f}, "
                                      f"BM25: {scores.get('bm25', 0):.3f}, "
                                      f"Rerank: {scores.get('rerank', 0):.3f}")
                    else:
                        print(f"  Run {run+1}: Failed - got {data.get('type')}")
                        
            except Exception as e:
                print(f"  Run {run+1}: Failed - {e}")
        
        if times:
            avg_time = sum(times) / len(times)
            print(f"  Average: {avg_time:.2f}s ({successes}/3 successful)")
        else:
            print(f"  Average: Failed all runs")

if __name__ == "__main__":
    print("🔬 Enhanced Citations Performance Measurement")
    print("=" * 50)
    asyncio.run(measure_citation_performance())