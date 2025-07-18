"""
Test Zotero sync progress bar in the frontend using Playwright.
"""
import asyncio
from playwright.async_api import async_playwright, Page, expect
import time


async def login_to_app(page: Page) -> None:
    """Login to the application."""
    await page.goto("http://localhost:3001/login")
    await page.fill('input[type="email"]', "test@example.com")
    await page.fill('input[type="password"]', "testpassword123")
    await page.click('button[type="submit"]')
    
    # Wait for navigation to complete
    await page.wait_for_url("**/dashboard", timeout=10000)
    print("✅ Logged in successfully")


async def navigate_to_zotero_settings(page: Page) -> None:
    """Navigate to Zotero settings page."""
    # Click on settings in navigation
    await page.click('a[href="/settings"]')
    await page.wait_for_url("**/settings")
    
    # Click on Zotero tab
    await page.click('text=Zotero')
    await page.wait_for_selector('text=Zotero Integration')
    print("✅ Navigated to Zotero settings")


async def capture_sync_progress(page: Page) -> None:
    """Capture screenshots of the sync progress."""
    screenshot_dir = "/Users/sschacht/Documents/Playgrounds/academic-citation-assistant/backend/tmp"
    
    # Take initial screenshot
    await page.screenshot(path=f"{screenshot_dir}/zotero_settings_initial.png", full_page=True)
    print("📸 Initial screenshot captured")
    
    # Find and click the sync button
    sync_button = page.locator('button:has-text("Sync Now")')
    await sync_button.wait_for(state="visible")
    
    # Start monitoring for progress bar before clicking
    progress_bar_found = False
    
    # Click sync button
    print("🔄 Clicking Sync Now button...")
    await sync_button.click()
    
    # Monitor for progress bar
    start_time = time.time()
    screenshot_count = 0
    
    while time.time() - start_time < 60:  # Monitor for up to 60 seconds
        try:
            # Check for progress bar elements
            progress_container = page.locator('.relative.w-full.bg-gray-200.rounded-full')
            if await progress_container.count() > 0:
                if not progress_bar_found:
                    print("✅ Progress bar appeared!")
                    progress_bar_found = True
                
                # Capture progress screenshot
                screenshot_count += 1
                await page.screenshot(
                    path=f"{screenshot_dir}/zotero_sync_progress_{screenshot_count}.png",
                    full_page=True
                )
                print(f"📸 Progress screenshot {screenshot_count} captured")
                
                # Try to read progress text
                progress_text = page.locator('text=/Processing \\d+/')
                if await progress_text.count() > 0:
                    text = await progress_text.inner_text()
                    print(f"📊 Progress: {text}")
            
            # Check if sync completed
            success_message = page.locator('text=/Sync completed/')
            if await success_message.count() > 0:
                print("✅ Sync completed successfully!")
                await page.screenshot(
                    path=f"{screenshot_dir}/zotero_sync_complete.png",
                    full_page=True
                )
                print("📸 Final screenshot captured")
                break
            
            # Check for error messages
            error_message = page.locator('.text-red-600')
            if await error_message.count() > 0:
                error_text = await error_message.inner_text()
                print(f"❌ Error detected: {error_text}")
                break
                
        except Exception as e:
            print(f"⚠️  Error during monitoring: {e}")
        
        await asyncio.sleep(0.5)
    
    if not progress_bar_found:
        print("⚠️  Progress bar was not detected during sync")
    
    # Capture console logs
    print("\n📋 Console logs:")
    console_logs = []
    page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))
    await asyncio.sleep(1)  # Give time for any final logs
    
    for log in console_logs[-10:]:  # Show last 10 logs
        print(f"   {log}")


async def test_sync_configuration(page: Page) -> None:
    """Test sync configuration changes."""
    print("\n=== Testing Sync Configuration ===")
    
    # Check current configuration
    config_text = await page.locator('.bg-gray-50').inner_text()
    print(f"Current configuration:\n{config_text}")
    
    # Test auto-sync toggle
    auto_sync_toggle = page.locator('input[type="checkbox"]').first
    is_checked = await auto_sync_toggle.is_checked()
    print(f"Auto-sync is {'enabled' if is_checked else 'disabled'}")
    
    # Toggle it
    await auto_sync_toggle.click()
    await asyncio.sleep(1)
    new_state = await auto_sync_toggle.is_checked()
    print(f"Auto-sync toggled to {'enabled' if new_state else 'disabled'}")


async def run_frontend_test():
    """Run the complete frontend test."""
    print("🚀 Starting Frontend Zotero Progress Bar Test")
    print("=" * 50)
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # Set to True for headless mode
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()
        
        try:
            # 1. Login
            print("\n1️⃣ Logging in to the application...")
            await login_to_app(page)
            
            # 2. Navigate to Zotero settings
            print("\n2️⃣ Navigating to Zotero settings...")
            await navigate_to_zotero_settings(page)
            
            # 3. Test sync configuration
            print("\n3️⃣ Testing sync configuration...")
            await test_sync_configuration(page)
            
            # 4. Capture sync progress
            print("\n4️⃣ Testing sync with progress monitoring...")
            await capture_sync_progress(page)
            
            # 5. Wait a bit to see final state
            print("\n5️⃣ Waiting to observe final state...")
            await asyncio.sleep(5)
            
            print("\n" + "=" * 50)
            print("✅ Frontend test completed successfully!")
            print(f"📸 Screenshots saved to: /Users/sschacht/Documents/Playgrounds/academic-citation-assistant/backend/tmp/")
            
        except Exception as e:
            print(f"\n❌ Frontend test failed: {e}")
            # Take error screenshot
            await page.screenshot(
                path="/Users/sschacht/Documents/Playgrounds/academic-citation-assistant/backend/tmp/error_screenshot.png",
                full_page=True
            )
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(run_frontend_test())