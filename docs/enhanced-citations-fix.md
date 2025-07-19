# Enhanced Citations Fix - v0.2.3

## Problem Summary
Enhanced citations were not delivering any results to the frontend when enabled. The system would connect but no suggestions would appear.

## Root Causes Identified

1. **UUID Serialization Error**: Paper IDs (UUIDs) were not being converted to strings before JSON serialization, causing "Object of type UUID is not JSON serializable" errors.

2. **Reranking Timeout**: The 30-second timeout for reranking was too long and consistently failing, preventing any results from being returned.

3. **WebSocket Query Parameter Issue**: FastAPI's `Query` dependency doesn't work correctly with WebSocket endpoints, causing additional serialization errors.

## Fixes Applied

### 1. UUID to String Conversion
- **Files**: `websocket.py`, `websocket_v2.py`
- **Fix**: Added `str()` conversion for `paper_id` and `chunk_id` fields
- **Example**: `"paperId": str(s.paper_id)` instead of `"paperId": s.paper_id`

### 2. Reduced Timeouts
- **File**: `citation_engine_v2.py`
- **Changes**:
  - Reranking timeout: 30s → 10s
  - BM25 fitting timeout: 30s → 15s  
  - Hybrid search timeout: 20s → 10s
- **Result**: Faster fallback to traditional ranking when reranking is slow

### 3. WebSocket Parameter Extraction
- **Files**: `websocket.py`, `websocket_v2.py`
- **Fix**: Removed `Query` imports and manually extract parameters from `websocket.query_params`
- **Example**: `user_id = dict(websocket.query_params).get("user_id")`

## Testing Enhanced Citations

### 1. Enable in UI
1. Open http://localhost:3000/editor
2. Click the gear icon in Citation Settings
3. Toggle "Enhanced Citations" ON
4. Select "Hybrid" search strategy
5. Enable "Smart Reranking" (optional)

### 2. Type Academic Text
Type sentences like:
- "Machine learning models have revolutionized natural language processing..."
- "Deep learning techniques for computer vision applications..."
- "Transformer architectures like BERT and GPT have shown remarkable performance..."

### 3. Verify Results
- Suggestions should appear within 2-5 seconds
- Check the connection status indicator (should be green)
- Enhanced citations show additional scores (BM25, Hybrid, Rerank)

### 4. Command Line Testing
```bash
# Test enhanced citations
python test_enhanced_citations.py

# Test frontend format
python test_frontend_format.py
```

## Performance Characteristics

1. **Vector Search Only**: ~1 second, returns 10-15 results
2. **Hybrid Search**: ~2 seconds, returns 10-15 results with better relevance
3. **With Reranking**: ~5-10 seconds (may timeout and fallback), highest quality results

## Monitoring

Check backend logs for any issues:
```bash
docker logs academic-citation-assistant-backend-1 -f | grep -E "(citation|enhanced|rerank)"
```

## Known Limitations

- Reranking may timeout on large result sets (falls back gracefully)
- First query with hybrid search is slower due to BM25 index fitting
- Results are limited to 15 citations to maintain UI performance