#!/usr/bin/env python3
"""Test Zotero API directly."""
import asyncio
import aiohttp

async def test_api():
    """Test Zotero API directly."""
    api_key = "VpsyLFU1ojlZruKic0Ye23OB"
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Fetch from COAI group without filters
        url = "https://api.zotero.org/groups/4965330/items"
        headers = {
            "Zotero-API-Key": api_key,
            "Zotero-API-Version": "3"
        }
        params = {
            "limit": 5,
            "start": 0
        }
        
        print("Test 1: Fetching from COAI without itemType filter...")
        async with session.get(url, headers=headers, params=params) as response:
            print(f"Status: {response.status}")
            print(f"Total Results: {response.headers.get('Total-Results')}")
            if response.status == 200:
                items = await response.json()
                print(f"Fetched {len(items)} items")
                if items:
                    print(f"First item type: {items[0].get('data', {}).get('itemType')}")
                    print(f"First item title: {items[0].get('data', {}).get('title')}")
        
        print("\n" + "="*50 + "\n")
        
        # Test 2: With itemType filter
        params["itemType"] = "journalArticle || book || bookSection || conferencePaper || report || thesis"
        
        print("Test 2: With itemType filter...")
        async with session.get(url, headers=headers, params=params) as response:
            print(f"Status: {response.status}")
            print(f"Total Results: {response.headers.get('Total-Results')}")
            if response.status == 200:
                items = await response.json()
                print(f"Fetched {len(items)} items")
        
        print("\n" + "="*50 + "\n")
        
        # Test 3: Check collection CPUVP4AQ
        params = {
            "limit": 100,
            "start": 0,
            "collection": "CPUVP4AQ"
        }
        
        print("Test 3: Fetching from collection CPUVP4AQ...")
        async with session.get(url, headers=headers, params=params) as response:
            print(f"Status: {response.status}")
            print(f"Total Results: {response.headers.get('Total-Results')}")
            if response.status == 200:
                items = await response.json()
                print(f"Fetched {len(items)} items from collection")

if __name__ == "__main__":
    asyncio.run(test_api())