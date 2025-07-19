"""Enhanced WebSocket endpoints with hybrid search and reranking support."""
from typing import Dict, Set, Optional
import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState
from app.core.config import settings
from app.services.citation_engine import CitationEngine
from app.services.citation_engine_v2 import EnhancedCitationEngine
from app.services.text_analysis import TextAnalysisService
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)


class EnhancedConnectionManager:
    """Enhanced WebSocket connection manager with feature flags."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_rate_limits: Dict[str, list] = {}
        self.user_preferences: Dict[str, dict] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str, preferences: Optional[dict] = None):
        """Accept and store a new WebSocket connection with preferences."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_rate_limits[user_id] = []
        self.user_preferences[user_id] = preferences or {
            "use_reranking": True,
            "search_strategy": "hybrid",
            "max_results": 10
        }
        logger.info(f"User {user_id} connected via WebSocket with preferences: {self.user_preferences[user_id]}")
        
    def disconnect(self, user_id: str):
        """Remove a WebSocket connection."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            if user_id in self.user_rate_limits:
                del self.user_rate_limits[user_id]
            if user_id in self.user_preferences:
                del self.user_preferences[user_id]
            logger.info(f"User {user_id} disconnected from WebSocket")
            
    async def send_personal_message(self, message: dict, user_id: str):
        """Send a message to a specific user."""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            if websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
                    logger.error(f"Message type: {type(message)}")
                    logger.error(f"Message content: {str(message)[:500]}...")
                    import traceback
                    logger.error(f"Full traceback: {traceback.format_exc()}")
                    self.disconnect(user_id)
                    
    def check_rate_limit(self, user_id: str) -> bool:
        """Check if user has exceeded rate limit (60 requests per minute)."""
        import time
        current_time = time.time()
        
        # Clean old timestamps (older than 1 minute)
        self.user_rate_limits[user_id] = [
            timestamp for timestamp in self.user_rate_limits.get(user_id, [])
            if current_time - timestamp < 60
        ]
        
        # Check if under limit
        if len(self.user_rate_limits.get(user_id, [])) >= settings.websocket_rate_limit:
            return False
            
        # Add current timestamp
        self.user_rate_limits[user_id].append(current_time)
        return True
    
    def update_preferences(self, user_id: str, preferences: dict):
        """Update user preferences for citation suggestions."""
        if user_id in self.user_preferences:
            self.user_preferences[user_id].update(preferences)


# Create a single instance to be shared
enhanced_manager = EnhancedConnectionManager()


async def websocket_citation_endpoint_v2(
    websocket: WebSocket
):
    """Enhanced WebSocket endpoint with configurable search strategies."""
    
    # Extract query parameters from the WebSocket URL
    query_params = dict(websocket.query_params)
    user_id = query_params.get("user_id")
    
    if not user_id:
        await websocket.close(code=1008, reason="Missing user_id parameter")
        return
    
    # Parse optional parameters with defaults
    use_enhanced = query_params.get("use_enhanced", "true").lower() == "true"
    use_reranking = query_params.get("use_reranking", "true").lower() == "true"
    search_strategy = query_params.get("search_strategy", "hybrid")
    
    # Set initial preferences
    preferences = {
        "use_enhanced": use_enhanced,
        "use_reranking": use_reranking,
        "search_strategy": search_strategy
    }
    
    await enhanced_manager.connect(websocket, user_id, preferences)
    
    # Get database session
    db_gen = get_db()
    db = await anext(db_gen)
    
    try:
        # Initialize services
        text_service = TextAnalysisService()
        
        # Choose citation engine based on preference
        if use_enhanced:
            citation_engine = EnhancedCitationEngine(db)
        else:
            citation_engine = CitationEngine(db)
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Check rate limit
            if not enhanced_manager.check_rate_limit(user_id):
                await enhanced_manager.send_personal_message({
                    "type": "error",
                    "message": "Rate limit exceeded. Please slow down."
                }, user_id)
                continue
            
            # Handle different message types
            if data.get("type") == "suggest":
                # Extract text and context
                text = data.get("text", "")
                context = data.get("context", {})
                
                # Skip if text is too short
                if len(text.strip()) < 10:
                    continue
                
                try:
                    # Analyze text to extract context
                    logger.info(f"Extracting context for text: {text[:50]}...")
                    text_context = text_service.extract_context(text, context)
                    
                    # Get user preferences
                    user_prefs = enhanced_manager.user_preferences.get(user_id, {})
                    logger.info(f"User preferences: {user_prefs}")
                    
                    # Get citation suggestions
                    if user_prefs.get("use_enhanced", True):
                        logger.info(f"Using enhanced citation engine with strategy: {user_prefs.get('search_strategy', 'hybrid')}, reranking: {user_prefs.get('use_reranking', True)}")
                        try:
                            suggestions = await citation_engine.get_suggestions_enhanced(
                                text=text_context.current_sentence,
                                context=text_context,
                                user_id=user_id,
                                use_reranking=user_prefs.get("use_reranking", True),
                                search_strategy=user_prefs.get("search_strategy", "hybrid")
                            )
                            logger.info(f"Enhanced citation engine returned {len(suggestions)} suggestions")
                        except Exception as e:
                            logger.error(f"Enhanced citation engine failed: {e}", exc_info=True)
                            raise
                        
                        # Format enhanced suggestions
                        results = [
                            {
                                "paperId": str(s.paper_id),  # Convert UUID to string
                                "title": s.title,
                                "authors": s.authors,
                                "year": s.year,
                                "abstract": s.abstract,
                                "confidence": float(s.confidence) if s.confidence is not None else 0.0,
                                "citationStyle": s.citation_style,
                                "displayText": s.display_text,
                                "chunkText": s.chunk_text[:200] + "..." if len(s.chunk_text) > 200 else s.chunk_text,
                                "chunkIndex": int(s.chunk_index) if s.chunk_index is not None else 0,
                                "chunkId": str(s.chunk_id) if s.chunk_id else '',  # Convert UUID to string
                                "sectionTitle": s.section_title,
                                "chunkType": s.chunk_type,
                                "pageStart": s.page_start,
                                "pageEnd": s.page_end,
                                "pageBoundaries": s.page_boundaries,
                                "scores": {
                                    "hybrid": float(s.hybrid_score) if s.hybrid_score is not None else 0.0,
                                    "bm25": float(s.bm25_score) if s.bm25_score is not None else 0.0,
                                    "rerank": float(s.rerank_score) if s.rerank_score is not None else 0.0,
                                    "confidence": float(s.confidence) if s.confidence is not None else 0.0
                                },
                                "metadata": {
                                    "sentenceCount": int(s.sentence_count) if s.sentence_count is not None else 0,
                                    "relevanceScores": {k: float(v) if v is not None else 0.0 for k, v in (s.relevance_scores or {}).items()}
                                }
                            }
                            for s in suggestions
                        ]
                    else:
                        # Use standard citation engine
                        suggestions = await citation_engine.get_suggestions(
                            text=text_context.current_sentence,
                            context=text_context,
                            user_id=user_id
                        )
                        
                        # Format standard suggestions
                        results = [
                            {
                                "paperId": str(s.paper_id),  # Convert UUID to string
                                "title": s.title,
                                "authors": s.authors,
                                "year": s.year,
                                "abstract": s.abstract,
                                "confidence": float(s.confidence) if s.confidence is not None else 0.0,
                                "citationStyle": s.citation_style,
                                "displayText": s.display_text,
                                "chunkText": s.chunk_text[:200] + "..." if len(s.chunk_text) > 200 else s.chunk_text,
                                "chunkIndex": int(s.chunk_index) if s.chunk_index is not None else 0,
                                "chunkId": str(s.chunk_id) if s.chunk_id else '',  # Convert UUID to string
                                "sectionTitle": s.section_title,
                                "pageStart": s.page_start,
                                "pageEnd": s.page_end,
                                "pageBoundaries": s.page_boundaries
                            }
                            for s in suggestions
                        ]
                    
                    # Send suggestions back to client
                    await enhanced_manager.send_personal_message({
                        "type": "suggestions",
                        "searchStrategy": user_prefs.get("search_strategy", "vector"),
                        "usedReranking": user_prefs.get("use_reranking", False) if user_prefs.get("use_enhanced", False) else False,
                        "results": results
                    }, user_id)
                    
                except Exception as e:
                    logger.error(f"Error processing suggestion request: {e}", exc_info=True)
                    await enhanced_manager.send_personal_message({
                        "type": "error",
                        "message": "Failed to process citation request"
                    }, user_id)
            
            elif data.get("type") == "update_preferences":
                # Update user preferences
                new_prefs = data.get("preferences", {})
                enhanced_manager.update_preferences(user_id, new_prefs)
                
                await enhanced_manager.send_personal_message({
                    "type": "preferences_updated",
                    "preferences": enhanced_manager.user_preferences.get(user_id, {})
                }, user_id)
                
            elif data.get("type") == "ping":
                # Respond to ping to keep connection alive
                await enhanced_manager.send_personal_message({
                    "type": "pong"
                }, user_id)
                
    except WebSocketDisconnect:
        enhanced_manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket connection: {e}", exc_info=True)
        enhanced_manager.disconnect(user_id)
    finally:
        # Clean up database session
        try:
            await db.close()
        except:
            pass