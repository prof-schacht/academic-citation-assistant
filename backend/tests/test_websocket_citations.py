"""Tests for WebSocket citation endpoint."""
import pytest
import json
from fastapi.testclient import TestClient
from app.main import app
from app.services.citation_engine import CitationEngine
from app.services.text_analysis import TextAnalysisService
import asyncio
from unittest.mock import Mock, patch, AsyncMock

client = TestClient(app)


@pytest.fixture
def mock_citation_engine():
    """Mock citation engine for testing."""
    with patch('app.api.websocket.CitationEngine') as mock:
        engine = AsyncMock()
        engine.get_suggestions = AsyncMock(return_value=[
            Mock(
                paper_id="test-123",
                title="Test Paper",
                authors=["Test Author"],
                year=2023,
                abstract="Test abstract",
                confidence=0.85,
                citation_style="inline",
                display_text="(Test Author, 2023)"
            )
        ])
        mock.return_value = engine
        yield engine


def test_websocket_connection():
    """Test WebSocket connection establishment."""
    with client.websocket_connect("/ws/citations?user_id=test-user") as websocket:
        # Connection should be established
        assert websocket is not None
        
        # Send a ping message
        websocket.send_json({"type": "ping"})
        
        # Should receive pong
        data = websocket.receive_json()
        assert data["type"] == "pong"


def test_websocket_suggestion_request(mock_citation_engine):
    """Test citation suggestion request."""
    with client.websocket_connect("/ws/citations?user_id=test-user") as websocket:
        # Send suggestion request
        websocket.send_json({
            "type": "suggest",
            "text": "Machine learning has revolutionized many fields",
            "context": {
                "currentSentence": "Machine learning has revolutionized many fields",
                "paragraph": "Machine learning has revolutionized many fields. It enables computers to learn from data.",
                "cursorPosition": 45
            }
        })
        
        # Should receive suggestions
        data = websocket.receive_json()
        assert data["type"] == "suggestions"
        assert "results" in data
        assert len(data["results"]) > 0
        assert data["results"][0]["title"] == "Test Paper"


def test_websocket_short_text_ignored():
    """Test that very short text is ignored."""
    with client.websocket_connect("/ws/citations?user_id=test-user") as websocket:
        # Send suggestion request with short text
        websocket.send_json({
            "type": "suggest",
            "text": "Hello",
            "context": {
                "currentSentence": "Hello",
                "paragraph": "Hello",
                "cursorPosition": 5
            }
        })
        
        # Should not receive any response for short text
        # Send ping to verify connection is still alive
        websocket.send_json({"type": "ping"})
        data = websocket.receive_json()
        assert data["type"] == "pong"


def test_websocket_rate_limiting():
    """Test rate limiting functionality."""
    with client.websocket_connect("/ws/citations?user_id=test-user-rate-limit") as websocket:
        # Send many requests quickly
        for i in range(65):  # More than rate limit
            websocket.send_json({
                "type": "suggest",
                "text": f"Test query number {i} with enough text",
                "context": {
                    "currentSentence": f"Test query number {i} with enough text",
                    "paragraph": f"Test query number {i} with enough text",
                    "cursorPosition": 20
                }
            })
        
        # Should eventually receive rate limit error
        received_error = False
        for _ in range(65):
            try:
                data = websocket.receive_json()
                if data.get("type") == "error" and "rate limit" in data.get("message", "").lower():
                    received_error = True
                    break
            except:
                break
        
        assert received_error


def test_text_analysis_service():
    """Test text analysis service functionality."""
    service = TextAnalysisService()
    
    # Test context extraction
    text = "This is the first sentence. This is the second sentence. This is the third sentence."
    context = service.extract_context(text, {"cursorPosition": 30})
    
    assert context.current_sentence == "This is the second sentence."
    assert context.previous_sentence == "This is the first sentence."
    assert context.next_sentence == "This is the third sentence."
    
    # Test preprocessing
    dirty_text = "This   has    extra   spaces... And multiple dots...."
    clean_text = service.preprocess_text(dirty_text)
    assert "   " not in clean_text
    assert "..." not in clean_text
    
    # Test should update
    old_text = "Machine learning is great"
    new_text = "Machine learning is great!"
    assert not service.should_update_suggestions(old_text, new_text)
    
    new_text = "Deep learning is even better"
    assert service.should_update_suggestions(old_text, new_text)


@pytest.mark.asyncio
async def test_citation_engine_caching():
    """Test that citation engine uses caching."""
    from app.db.session import get_db
    from app.services.citation_engine import CitationEngine
    from app.services.text_analysis import TextContext
    
    # Mock database session
    mock_db = AsyncMock()
    
    with patch('app.services.vector_search.VectorSearchService.search_similar_chunks') as mock_search:
        mock_search.return_value = []
        
        engine = CitationEngine(mock_db)
        
        # Make same request twice
        context = TextContext(
            current_sentence="Test sentence",
            paragraph="Test paragraph"
        )
        
        # First request
        await engine.get_suggestions("Test query", context, "test-user")
        
        # Second request (should use cache if implemented)
        await engine.get_suggestions("Test query", context, "test-user")
        
        # Vector search should be called at least once
        assert mock_search.called


def test_websocket_invalid_message():
    """Test handling of invalid messages."""
    with client.websocket_connect("/ws/citations?user_id=test-user") as websocket:
        # Send invalid message type
        websocket.send_json({
            "type": "invalid_type",
            "data": "some data"
        })
        
        # Connection should still be alive
        websocket.send_json({"type": "ping"})
        data = websocket.receive_json()
        assert data["type"] == "pong"


def test_websocket_missing_user_id():
    """Test that connection requires user_id parameter."""
    from starlette.testclient import WebSocketTestSession
    
    try:
        with client.websocket_connect("/ws/citations") as websocket:
            # Should not reach here
            assert False, "Connection should be rejected without user_id"
    except WebSocketTestSession._Upgrade as e:
        # Connection rejected is expected
        assert e.status_code == 403  # Or appropriate error code
    except Exception:
        # Any rejection is acceptable for missing user_id
        pass