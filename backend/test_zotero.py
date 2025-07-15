#!/usr/bin/env python3
"""Test Zotero configuration."""
import asyncio
import httpx
import json

async def test_zotero_config():
    """Test the Zotero configuration endpoint."""
    base_url = "http://localhost:8000/api"
    
    # Test data
    config_data = {
        "api_key": "VpsyLFU1ojlZruKic0Ye23OB",
        "zotero_user_id": "5008235",
        "auto_sync_enabled": False,
        "sync_interval_minutes": 30
    }
    
    async with httpx.AsyncClient() as client:
        # First test status endpoint
        print("Testing /zotero/status endpoint...")
        try:
            response = await client.get(f"{base_url}/zotero/status")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # Test configuration endpoint
        print("Testing /zotero/configure endpoint...")
        try:
            response = await client.post(
                f"{base_url}/zotero/configure",
                json=config_data,
                headers={"Content-Type": "application/json"}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 400:
                print("\nError details:")
                try:
                    error_data = response.json()
                    print(json.dumps(error_data, indent=2))
                except:
                    pass
                    
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_zotero_config())