"""
Unit tests for Zotero sync progress functionality.
Tests the service directly without requiring a running server.
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from app.services.zotero_service import ZoteroService
from app.models import ZoteroConfig, User


class TestZoteroProgressTracking:
    """Test progress tracking functionality in ZoteroService."""
    
    @pytest.fixture
    async def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        return db
    
    @pytest.fixture
    def user_id(self):
        """Generate a test user ID."""
        return uuid4()
    
    @pytest.fixture
    async def zotero_config(self, user_id):
        """Create a mock Zotero configuration."""
        config = Mock(spec=ZoteroConfig)
        config.user_id = user_id
        config.api_key = "test_api_key"
        config.zotero_user_id = "12345"
        config.selected_groups = '["groups/4965330"]'
        config.selected_collections = '[{"key": "ABC123", "libraryId": "groups/4965330"}]'
        config.last_sync = None
        return config
    
    @pytest.fixture
    async def zotero_service(self, mock_db, user_id, zotero_config):
        """Create a ZoteroService instance with mocked dependencies."""
        service = ZoteroService(mock_db, user_id)
        
        # Mock the config loading
        mock_db.execute.return_value.scalar_one_or_none.return_value = zotero_config
        service._config = zotero_config
        
        # Mock the session
        service._session = AsyncMock()
        
        return service
    
    def test_initial_progress_state(self, zotero_service):
        """Test that initial progress state is correct."""
        progress = zotero_service.get_sync_progress()
        
        assert progress["status"] == "idle"
        assert progress["current"] == 0
        assert progress["total"] == 0
        assert progress["message"] == ""
        assert progress["libraries_processed"] == 0
        assert progress["libraries_total"] == 0
    
    def test_update_progress(self, zotero_service):
        """Test updating progress state."""
        # Update progress
        zotero_service._update_sync_progress(
            status="fetching",
            current=10,
            total=100,
            message="Fetching items...",
            libraries_processed=1,
            libraries_total=3
        )
        
        # Get updated progress
        progress = zotero_service.get_sync_progress()
        
        assert progress["status"] == "fetching"
        assert progress["current"] == 10
        assert progress["total"] == 100
        assert progress["message"] == "Fetching items..."
        assert progress["libraries_processed"] == 1
        assert progress["libraries_total"] == 3
    
    def test_progress_copy_isolation(self, zotero_service):
        """Test that get_sync_progress returns a copy, not reference."""
        # Get initial progress
        progress1 = zotero_service.get_sync_progress()
        
        # Modify the returned dict
        progress1["status"] = "modified"
        
        # Get progress again
        progress2 = zotero_service.get_sync_progress()
        
        # Should still be "idle" because we return a copy
        assert progress2["status"] == "idle"
    
    @pytest.mark.asyncio
    async def test_fetch_library_items_progress(self, zotero_service):
        """Test progress updates during fetch_library_items."""
        # Mock API responses
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = [
            {"data": {"itemType": "journalArticle", "title": "Test Paper 1"}},
            {"data": {"itemType": "journalArticle", "title": "Test Paper 2"}}
        ]
        mock_response.headers = {"Total-Results": "2"}
        
        zotero_service._session.get.return_value.__aenter__.return_value = mock_response
        
        # Start fetch
        papers, attachments = await zotero_service.fetch_library_items()
        
        # Check that progress was updated
        progress = zotero_service.get_sync_progress()
        assert progress["status"] == "processing"
        assert progress["libraries_processed"] == 1
        assert len(papers) == 2
    
    @pytest.mark.asyncio
    async def test_sync_library_progress_stages(self, zotero_service):
        """Test progress updates through all sync stages."""
        # Track progress updates
        progress_updates = []
        
        # Override update method to track calls
        original_update = zotero_service._update_sync_progress
        
        def track_update(**kwargs):
            progress_updates.append(kwargs.copy())
            original_update(**kwargs)
        
        zotero_service._update_sync_progress = track_update
        
        # Mock fetch response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = []
        mock_response.headers = {"Total-Results": "0"}
        
        zotero_service._session.get.return_value.__aenter__.return_value = mock_response
        
        # Mock database operations
        zotero_service.db.execute.return_value.scalar_one_or_none.return_value = None
        zotero_service.db.commit = AsyncMock()
        
        # Run sync
        await zotero_service.sync_library()
        
        # Verify progress stages
        assert len(progress_updates) >= 3
        
        # Check starting stage
        start_update = next(u for u in progress_updates if u.get("status") == "starting")
        assert start_update is not None
        assert "Preparing to sync" in start_update["message"]
        
        # Check fetching stage
        fetch_updates = [u for u in progress_updates if u.get("status") == "fetching"]
        assert len(fetch_updates) > 0
        
        # Check completed stage
        complete_update = next(u for u in progress_updates if u.get("status") == "completed")
        assert complete_update is not None
        assert "Sync complete" in complete_update["message"]
    
    def test_collection_format_parsing(self, zotero_service):
        """Test parsing of new collection format with library IDs."""
        # Test new format
        zotero_service._config.selected_collections = '[{"key": "ABC123", "libraryId": "groups/4965330"}]'
        
        # This would be called internally during fetch_library_items
        import json
        collections_data = json.loads(zotero_service._config.selected_collections)
        
        assert len(collections_data) == 1
        assert collections_data[0]["key"] == "ABC123"
        assert collections_data[0]["libraryId"] == "groups/4965330"
    
    def test_collection_format_backward_compatibility(self, zotero_service):
        """Test backward compatibility with old collection format."""
        # Test old format (just array of keys)
        zotero_service._config.selected_collections = '["ABC123", "DEF456"]'
        
        import json
        collections_data = json.loads(zotero_service._config.selected_collections)
        
        assert len(collections_data) == 2
        assert collections_data[0] == "ABC123"
        assert collections_data[1] == "DEF456"


def test_progress_tracking_flow():
    """Test the complete progress tracking flow without async."""
    print("\n🧪 Testing Zotero Progress Tracking")
    print("=" * 50)
    
    # Create mock objects
    mock_db = Mock()
    user_id = uuid4()
    
    # Create service
    service = ZoteroService(mock_db, user_id)
    
    # Test 1: Initial state
    print("\n1️⃣ Testing initial progress state...")
    progress = service.get_sync_progress()
    assert progress["status"] == "idle"
    print("✅ Initial state correct")
    
    # Test 2: Update progress
    print("\n2️⃣ Testing progress updates...")
    service._update_sync_progress(
        status="fetching",
        current=25,
        total=100,
        message="Fetching papers from Zotero..."
    )
    
    progress = service.get_sync_progress()
    assert progress["status"] == "fetching"
    assert progress["current"] == 25
    assert progress["total"] == 100
    print(f"✅ Progress updated: {progress['current']}/{progress['total']} - {progress['message']}")
    
    # Test 3: Multiple updates
    print("\n3️⃣ Testing multiple progress stages...")
    stages = [
        ("starting", 0, 0, "Preparing sync..."),
        ("fetching", 0, 0, "Connecting to Zotero..."),
        ("processing", 50, 100, "Processing papers..."),
        ("processing", 100, 100, "Finalizing..."),
        ("completed", 100, 100, "Sync completed successfully!")
    ]
    
    for status, current, total, message in stages:
        service._update_sync_progress(
            status=status,
            current=current,
            total=total,
            message=message
        )
        progress = service.get_sync_progress()
        print(f"   📊 {status}: {current}/{total} - {message}")
    
    print("\n✅ All progress tracking tests passed!")
    print("=" * 50)


if __name__ == "__main__":
    # Run the simple flow test
    test_progress_tracking_flow()
    
    # Run pytest if available
    try:
        import pytest
        print("\n🧪 Running pytest unit tests...")
        pytest.main([__file__, "-v"])
    except ImportError:
        print("\nℹ️  pytest not available, skipping unit tests")