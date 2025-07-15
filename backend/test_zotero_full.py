#!/usr/bin/env python3
"""Test full Zotero integration including groups."""
import asyncio
import httpx
import json

async def test_full_zotero():
    """Test the full Zotero integration."""
    base_url = "http://localhost:8000/api"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Configure Zotero
        print("1. Configuring Zotero...")
        config_data = {
            "api_key": "VpsyLFU1ojlZruKic0Ye23OB",
            "zotero_user_id": "5008235",
            "auto_sync_enabled": True,
            "sync_interval_minutes": 30
        }
        
        response = await client.post(
            f"{base_url}/zotero/configure",
            json=config_data
        )
        print(f"Configure Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code != 200:
            print("Configuration failed!")
            return
            
        print("\n" + "="*50 + "\n")
        
        # 2. Get groups
        print("2. Fetching Zotero groups...")
        response = await client.get(f"{base_url}/zotero/groups")
        print(f"Groups Status: {response.status_code}")
        
        if response.status_code == 200:
            groups = response.json()
            print(f"Found {len(groups)} groups:")
            for group in groups:
                print(f"  - {group['name']} (ID: {group['id']})")
        
        print("\n" + "="*50 + "\n")
        
        # 3. Test sync
        print("3. Testing sync...")
        response = await client.post(f"{base_url}/zotero/sync")
        print(f"Sync Status: {response.status_code}")
        
        if response.status_code == 200:
            sync_result = response.json()
            print(f"Sync Result: {json.dumps(sync_result, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_full_zotero())