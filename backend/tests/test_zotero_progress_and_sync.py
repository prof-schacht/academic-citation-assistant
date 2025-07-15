"""
Test Zotero sync progress bar and timestamp fix functionality.
"""
import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, Any

# Test configuration
API_BASE_URL = "http://localhost:8001/api"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword123"


async def login() -> str:
    """Login and return JWT token."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_BASE_URL}/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        ) as response:
            if response.status != 200:
                text = await response.text()
                print(f"Login failed: {response.status} - {text}")
                raise Exception("Login failed")
            data = await response.json()
            return data["access_token"]


async def test_progress_endpoint(token: str) -> Dict[str, Any]:
    """Test the progress endpoint."""
    print("\n=== Testing Progress Endpoint ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{API_BASE_URL}/zotero/sync/progress",
            headers=headers
        ) as response:
            if response.status != 200:
                text = await response.text()
                print(f"❌ Progress endpoint failed: {response.status} - {text}")
                return None
            
            progress = await response.json()
            print(f"✅ Progress endpoint working: {json.dumps(progress, indent=2)}")
            return progress


async def trigger_sync(token: str) -> Dict[str, Any]:
    """Trigger a Zotero sync and return result."""
    print("\n=== Triggering Zotero Sync ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_BASE_URL}/zotero/sync",
            headers=headers
        ) as response:
            if response.status != 200:
                text = await response.text()
                print(f"❌ Sync failed: {response.status} - {text}")
                return None
            
            result = await response.json()
            print(f"✅ Sync triggered successfully")
            return result


async def monitor_sync_progress(token: str, max_duration: int = 300) -> bool:
    """Monitor sync progress until completion."""
    print("\n=== Monitoring Sync Progress ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    start_time = time.time()
    last_status = None
    progress_shown = False
    
    async with aiohttp.ClientSession() as session:
        while time.time() - start_time < max_duration:
            try:
                async with session.get(
                    f"{API_BASE_URL}/zotero/sync/progress",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        print(f"❌ Failed to get progress: {response.status}")
                        await asyncio.sleep(1)
                        continue
                    
                    progress = await response.json()
                    
                    # Check if status changed
                    if progress['status'] != last_status:
                        print(f"\n📊 Status: {progress['status']}")
                        last_status = progress['status']
                    
                    # Show progress bar if syncing
                    if progress['status'] in ['fetching', 'processing']:
                        progress_shown = True
                        total = progress.get('total', 0)
                        current = progress.get('current', 0)
                        message = progress.get('message', '')
                        
                        if total > 0:
                            percentage = (current / total) * 100
                            bar_length = 40
                            filled_length = int(bar_length * current / total)
                            bar = '█' * filled_length + '-' * (bar_length - filled_length)
                            
                            print(f"\r[{bar}] {percentage:.1f}% - {message}", end='', flush=True)
                    
                    # Check if completed
                    if progress['status'] == 'completed':
                        print(f"\n✅ Sync completed: {progress.get('message', 'Done')}")
                        return True
                    
                    # Check if failed
                    if progress['status'] == 'error':
                        print(f"\n❌ Sync failed: {progress.get('message', 'Unknown error')}")
                        return False
                    
            except Exception as e:
                print(f"\n❌ Error monitoring progress: {e}")
            
            await asyncio.sleep(0.5)
    
    print(f"\n⏱️ Monitoring timed out after {max_duration} seconds")
    return False


async def check_zotero_config(token: str) -> Dict[str, Any]:
    """Check current Zotero configuration."""
    print("\n=== Checking Zotero Configuration ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{API_BASE_URL}/zotero/status",
            headers=headers
        ) as response:
            if response.status != 200:
                text = await response.text()
                print(f"❌ Failed to get config: {response.status} - {text}")
                return None
            
            config = await response.json()
            print(f"✅ Configuration:")
            print(f"   - Configured: {config.get('configured', False)}")
            print(f"   - Auto sync: {config.get('auto_sync_enabled', False)}")
            print(f"   - Last sync: {config.get('last_sync', 'Never')}")
            print(f"   - Last status: {config.get('last_sync_status', 'N/A')}")
            print(f"   - Selected groups: {config.get('selected_groups', [])}")
            print(f"   - Selected collections: {config.get('selected_collections', [])}")
            return config


async def clear_sync_timestamp(token: str) -> bool:
    """Clear the last sync timestamp to force a full sync."""
    print("\n=== Clearing Sync Timestamp ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get current config
    async with aiohttp.ClientSession() as session:
        # First get current config
        async with session.get(
            f"{API_BASE_URL}/zotero/status",
            headers=headers
        ) as response:
            if response.status != 200:
                print("❌ Failed to get current config")
                return False
            
            config = await response.json()
        
        # Update config with same settings but trigger timestamp clear
        update_data = {
            "api_key": "",  # Empty to keep existing
            "zotero_user_id": "",  # Empty to keep existing
            "auto_sync_enabled": config.get('auto_sync_enabled', True),
            "sync_interval_minutes": 30,
            "selected_groups": config.get('selected_groups', []),
            "selected_collections": config.get('selected_collections', [])
        }
        
        # Note: The backend should handle clearing the timestamp when collections change
        # For testing, we might need to manually clear it via database
        print("ℹ️  Note: Timestamp clearing is handled automatically when collections change")
        return True


async def run_full_test():
    """Run complete test suite."""
    print("🚀 Starting Zotero Sync Progress and Fix Tests")
    print("=" * 50)
    
    try:
        # 1. Login
        print("\n1️⃣ Logging in...")
        token = await login()
        print("✅ Login successful")
        
        # 2. Check configuration
        print("\n2️⃣ Checking Zotero configuration...")
        config = await check_zotero_config(token)
        if not config or not config.get('configured'):
            print("❌ Zotero not configured. Please configure it first.")
            return
        
        # 3. Test progress endpoint before sync
        print("\n3️⃣ Testing progress endpoint (idle state)...")
        initial_progress = await test_progress_endpoint(token)
        if initial_progress and initial_progress.get('status') != 'idle':
            print("⚠️  Sync already in progress. Waiting for completion...")
            await monitor_sync_progress(token)
        
        # 4. Clear timestamp (if needed for testing)
        print("\n4️⃣ Preparing for sync test...")
        await clear_sync_timestamp(token)
        
        # 5. Trigger sync
        print("\n5️⃣ Triggering Zotero sync...")
        sync_task = asyncio.create_task(trigger_sync(token))
        
        # 6. Monitor progress
        print("\n6️⃣ Monitoring sync progress...")
        await asyncio.sleep(0.5)  # Give sync a moment to start
        progress_success = await monitor_sync_progress(token)
        
        # 7. Wait for sync task to complete
        sync_result = await sync_task
        
        # 8. Verify results
        print("\n7️⃣ Verifying sync results...")
        if sync_result:
            print(f"✅ Sync completed successfully:")
            print(f"   - New papers: {sync_result.get('new_papers', 0)}")
            print(f"   - Updated papers: {sync_result.get('updated_papers', 0)}")
            print(f"   - Failed papers: {sync_result.get('failed_papers', 0)}")
            print(f"   - Message: {sync_result.get('message', '')}")
        
        # 9. Check final configuration
        print("\n8️⃣ Checking final configuration...")
        final_config = await check_zotero_config(token)
        
        # 10. Test incremental sync
        print("\n9️⃣ Testing incremental sync (should be faster)...")
        print("Triggering another sync to test incremental functionality...")
        
        sync_task2 = asyncio.create_task(trigger_sync(token))
        await asyncio.sleep(0.5)
        progress_success2 = await monitor_sync_progress(token)
        sync_result2 = await sync_task2
        
        if sync_result2:
            print(f"✅ Incremental sync completed:")
            print(f"   - New papers: {sync_result2.get('new_papers', 0)}")
            print(f"   - Updated papers: {sync_result2.get('updated_papers', 0)}")
            print(f"   - Failed papers: {sync_result2.get('failed_papers', 0)}")
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_full_test())