"""WebSocket endpoints for real-time citation suggestions."""
from typing import Dict, Set
import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState
from app.core.config import settings
from app.services.citation_engine import CitationEngine
from app.services.text_analysis import TextAnalysisService
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for all users."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_rate_limits: Dict[str, list] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_rate_limits[user_id] = []
        logger.info(f"User {user_id} connected via WebSocket")
        
    def disconnect(self, user_id: str):
        """Remove a WebSocket connection."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            if user_id in self.user_rate_limits:
                del self.user_rate_limits[user_id]
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


# Create a single instance to be shared
manager = ConnectionManager()


async def websocket_citation_endpoint(
    websocket: WebSocket
):
    """WebSocket endpoint for real-time citation suggestions."""
    # Extract query parameters from the WebSocket URL
    query_params = dict(websocket.query_params)
    user_id = query_params.get("user_id")
    
    if not user_id:
        await websocket.close(code=1008, reason="Missing user_id parameter")
        return
    
    await manager.connect(websocket, user_id)
    
    # Get database session
    db_gen = get_db()
    db = await anext(db_gen)
    
    try:
        # Initialize services
        text_service = TextAnalysisService()
        citation_engine = CitationEngine(db)
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Check rate limit
            if not manager.check_rate_limit(user_id):
                await manager.send_personal_message({
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
                    text_context = text_service.extract_context(text, context)
                    
                    # Get citation suggestions
                    suggestions = await citation_engine.get_suggestions(
                        text=text_context.current_sentence,
                        context=text_context,
                        user_id=user_id
                    )
                    
                    # Send suggestions back to client
                    await manager.send_personal_message({
                        "type": "suggestions",
                        "results": [
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
                                "sectionTitle": s.section_title
                            }
                            for s in suggestions
                        ]
                    }, user_id)
                    
                except Exception as e:
                    logger.error(f"Error processing suggestion request: {e}")
                    await manager.send_personal_message({
                        "type": "error",
                        "message": "Failed to process citation request"
                    }, user_id)
                    
            elif data.get("type") == "ping":
                # Respond to ping to keep connection alive
                await manager.send_personal_message({
                    "type": "pong"
                }, user_id)
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(user_id)
    finally:
        # Clean up database connection
        try:
            await db_gen.aclose()
        except:
            pass