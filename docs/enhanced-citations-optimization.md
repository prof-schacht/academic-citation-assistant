# Enhanced Citations Performance Optimization

## Problem
Enhanced citations with reranking were consistently timing out after 10 seconds, making the feature unusable. Falling back to traditional ranking defeated the purpose of having enhanced citations.

## Root Cause Analysis
1. **Too many candidates**: System was fetching 150 results for reranking
2. **Inefficient reranking**: All 150 results were being reranked before limiting to top 50
3. **Double computation**: Context scoring added another cross-encoder pass
4. **Small batch size**: Default batch size of 32 meant 5 batches for 150 results
5. **CPU processing**: Cross-encoder running on CPU is inherently slow

## Optimizations Applied

### 1. Reduced Search Candidates
- **Before**: 150 results fetched when reranking enabled
- **After**: 30 results fetched (80% reduction)
- **File**: `citation_engine_v2.py` line 111

### 2. Limited Reranking Scope
- **Before**: Rerank all results, then take top 50
- **After**: Take top 20 results first, then rerank only those
- **Files**: 
  - `citation_engine_v2.py` line 312: top_k reduced from 50 to 20
  - `reranking_service.py` lines 227-230: Pre-filter results before reranking

### 3. Increased Batch Size
- **Before**: Batch size of 32 (5 batches for 150 items)
- **After**: Batch size of 64 (1 batch for most queries)
- **File**: `citation_engine_v2.py` line 60

### 4. Disabled Context Scoring
- **Why**: Context scoring doubled processing time by running cross-encoder twice
- **File**: `reranking_service.py` lines 261-266: Commented out context scoring

### 5. Made Reranking Opt-in
- **Before**: Reranking enabled by default
- **After**: Reranking disabled by default, users can enable if needed
- **File**: `CitationSettings.tsx` line 62: Changed default from `true` to `false`

## Performance Results

### Before Optimization
- Reranking consistently timed out after 10 seconds
- Fell back to traditional ranking
- Enhanced citations provided no benefit

### After Optimization
- **Vector search**: ~0.5 seconds, 13 results
- **Hybrid search**: ~0.6 seconds, 14 results  
- **Hybrid + Reranking**: ~1.1 seconds, 5-20 high-quality results

## User Experience Improvements

1. **Faster Response**: Results appear in 1-2 seconds instead of timing out
2. **Better Defaults**: Most users get good results without reranking
3. **Clear Expectations**: UI shows reranking adds "2-5 seconds latency"
4. **Optional Enhancement**: Power users can enable reranking when quality matters more than speed

## Recommendations for Further Optimization

1. **GPU Support**: Enable CUDA if available for 5-10x speedup
2. **Model Selection**: Consider lighter reranking models like MiniLM-L6
3. **Caching**: Cache reranking scores for common queries
4. **Async Processing**: Show initial results, then update with reranked results
5. **Batch Queries**: Process multiple queries together for efficiency