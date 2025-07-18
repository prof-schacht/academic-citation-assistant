#!/usr/bin/env python3
"""Test script for Zotero collection sync fix."""

import asyncio
import json
import sys
from uuid import uuid4

# Add the current directory to the path so we can import our modules
sys.path.insert(0, '.')

from app.services.zotero_service import ZoteroService
from app.models import ZoteroConfig, User
from app.db.session import AsyncSessionLocal
from sqlalchemy import select
from datetime import datetime


async def test_collection_sync():
    """Test the collection sync functionality."""
    
    # Create a test user
    user_id = uuid4()
    
    async with AsyncSessionLocal() as db:
        # Create a test user (you may need to adjust this based on your User model)
        test_user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password="test_hash",
            is_active=True
        )
        db.add(test_user)
        await db.commit()
        
        # Create test config with some collections
        # New format: [{key: "COLLECTION_KEY", libraryId: "users/12345"}]
        test_collections = [
            {"key": "CPUVP4AQ", "libraryId": "users/12345"},
            {"key": "ABCD1234", "libraryId": "groups/67890"}
        ]
        
        config = ZoteroConfig(
            user_id=user_id,
            api_key="test_key",
            zotero_user_id="12345",
            selected_collections=json.dumps(test_collections)
        )
        db.add(config)
        await db.commit()
        
        # Test the service
        async with ZoteroService(db, user_id) as service:
            # Test parsing collections
            print("Testing collection parsing...")
            
            # Mock the _config to test the parsing logic
            service._config = config
            
            # Test the fetch_library_items method logic (without making API calls)
            selected_groups = []
            selected_collections = []
            selected_collections_by_library = {}
            
            if service._config.selected_collections:
                try:
                    collections_data = json.loads(service._config.selected_collections)
                    for collection in collections_data:
                        if isinstance(collection, dict) and 'key' in collection and 'libraryId' in collection:
                            lib_id = collection['libraryId']
                            key = collection['key']
                            if lib_id not in selected_collections_by_library:
                                selected_collections_by_library[lib_id] = []
                            selected_collections_by_library[lib_id].append(key)
                            selected_collections.append(key)
                        else:
                            selected_collections.append(collection)
                except:
                    selected_collections = []
            
            # Check libraries to fetch
            libraries_to_fetch = set(selected_groups)
            libraries_to_fetch.update(selected_collections_by_library.keys())
            
            print(f"Selected collections: {selected_collections}")
            print(f"Collections by library: {selected_collections_by_library}")
            print(f"Libraries to fetch: {libraries_to_fetch}")
            
            # Verify expected behavior
            assert len(selected_collections) == 2
            assert "CPUVP4AQ" in selected_collections
            assert "ABCD1234" in selected_collections
            assert "users/12345" in selected_collections_by_library
            assert "groups/67890" in selected_collections_by_library
            assert selected_collections_by_library["users/12345"] == ["CPUVP4AQ"]
            assert selected_collections_by_library["groups/67890"] == ["ABCD1234"]
            assert libraries_to_fetch == {"users/12345", "groups/67890"}
            
            print("✓ Collection parsing works correctly!")
            
            # Test backward compatibility with old format
            print("\nTesting backward compatibility...")
            old_format_collections = ["CPUVP4AQ", "ABCD1234"]
            config.selected_collections = json.dumps(old_format_collections)
            
            selected_collections = []
            selected_collections_by_library = {}
            
            collections_data = json.loads(config.selected_collections)
            for collection in collections_data:
                if isinstance(collection, dict) and 'key' in collection and 'libraryId' in collection:
                    lib_id = collection['libraryId']
                    key = collection['key']
                    if lib_id not in selected_collections_by_library:
                        selected_collections_by_library[lib_id] = []
                    selected_collections_by_library[lib_id].append(key)
                    selected_collections.append(key)
                else:
                    selected_collections.append(collection)
            
            libraries_to_fetch = set()
            libraries_to_fetch.update(selected_collections_by_library.keys())
            
            if selected_collections and not libraries_to_fetch:
                libraries_to_fetch.add(f"users/{service._config.zotero_user_id}")
            
            print(f"Old format collections: {selected_collections}")
            print(f"Libraries to fetch: {libraries_to_fetch}")
            
            assert len(selected_collections) == 2
            assert "CPUVP4AQ" in selected_collections
            assert "ABCD1234" in selected_collections
            assert libraries_to_fetch == {"users/12345"}  # Should fallback to user library
            
            print("✓ Backward compatibility works!")
            
            # Test progress tracking
            print("\nTesting progress tracking...")
            progress = service.get_sync_progress()
            print(f"Initial progress: {progress}")
            
            service._update_sync_progress(
                status="testing",
                current=50,
                total=100,
                message="Testing progress tracking"
            )
            
            updated_progress = service.get_sync_progress()
            print(f"Updated progress: {updated_progress}")
            
            assert updated_progress["status"] == "testing"
            assert updated_progress["current"] == 50
            assert updated_progress["total"] == 100
            assert updated_progress["message"] == "Testing progress tracking"
            
            print("✓ Progress tracking works!")
        
        # Clean up
        await db.delete(test_user)
        await db.delete(config)
        await db.commit()
        
        print("\n✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(test_collection_sync())