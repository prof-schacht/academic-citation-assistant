#!/usr/bin/env python3
"""Test syncing a small group to verify functionality."""
import asyncio
import httpx
import json

async def test_small_sync():
    """Test with a smaller group."""
    async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minute timeout
        # Let's try "SoSe21 - KFZ Schein" which might be smaller
        test_group = "groups/2893998"
        
        print(f"Configuring to sync only group: {test_group}")
        
        # Update config
        config_data = {
            "auto_sync_enabled": False,
            "sync_interval_minutes": 30,
            "selected_groups": [test_group],
            "selected_collections": []
        }
        
        response = await client.post(
            "http://localhost:8000/api/zotero/configure",
            json=config_data
        )
        
        if response.status_code != 200:
            print(f"Failed to update config: {response.status_code}")
            return
            
        print("Configuration updated successfully!")
        
        # Now sync
        print("\nStarting sync...")
        sync_response = await client.post(
            "http://localhost:8000/api/zotero/sync",
            json={"force_full_sync": True}
        )
        
        print(f"Sync response: {sync_response.json()}")
        
        # Check logs
        print("\nChecking logs...")
        logs_response = await client.get(
            "http://localhost:8000/api/logs/?category=ZOTERO_SYNC&per_page=5"
        )
        logs = logs_response.json()
        for log in logs['logs'][:3]:
            print(f"  {log['created_at']}: {log['message']}")

if __name__ == "__main__":
    asyncio.run(test_small_sync())