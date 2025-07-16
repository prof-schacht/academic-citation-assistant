#!/usr/bin/env python3
"""Test updating Zotero configuration with a group."""
import asyncio
import httpx
import json

async def test_update_config():
    """Test updating Zotero config with AI-Audit group."""
    
    # Find AI-Audit group ID
    async with httpx.AsyncClient() as client:
        # First get available groups
        response = await client.get("http://localhost:8000/api/zotero/groups")
        groups = response.json()
        
        print("Available groups:")
        for group in groups:
            print(f"  - {group['name']}: {group['id']}")
        
        # Find a group to test with (let's use COAI as an example)
        test_group_id = "groups/4965330"  # COAI group
        
        # Update configuration to select this group
        config_data = {
            "apiKey": "",  # Empty for update
            "zoteroUserId": "",  # Empty for update
            "autoSyncEnabled": True,
            "syncIntervalMinutes": 30,
            "selectedGroups": [test_group_id],
            "selectedCollections": []
        }
        
        print(f"\nUpdating config to select group: {test_group_id}")
        print(f"Config data: {json.dumps(config_data, indent=2)}")
        
        response = await client.post(
            "http://localhost:8000/api/zotero/configure",
            json=config_data
        )
        
        if response.status_code == 200:
            print("\nConfiguration updated successfully!")
            result = response.json()
            print(f"Selected groups: {result.get('selected_groups', 'N/A')}")
            print(f"Selected collections: {result.get('selected_collections', 'N/A')}")
        else:
            print(f"\nError updating config: {response.status_code}")
            print(response.text)
        
        # Verify the update
        print("\nVerifying configuration...")
        response = await client.get("http://localhost:8000/api/zotero/status")
        status = response.json()
        print(f"Current selected groups: {status['selected_groups']}")
        print(f"Current selected collections: {status['selected_collections']}")

if __name__ == "__main__":
    asyncio.run(test_update_config())