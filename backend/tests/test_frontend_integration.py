"""Test frontend integration with Zotero sync progress bar."""
import asyncio
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_frontend_progress_bar():
    """Test that the frontend progress bar works with Zotero sync."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Navigate to the app
            await page.goto("http://localhost:3000")
            await page.wait_for_load_state("networkidle")
            
            # Take a screenshot of the initial state
            await page.screenshot(path="tests/screenshots/initial_state.png")
            logger.info("Screenshot saved: initial_state.png")
            
            # Check if login is required
            if await page.is_visible("text=Sign In"):
                logger.info("Login required - skipping UI test")
                return
            
            # Look for Zotero sync button
            sync_button = await page.query_selector("button:has-text('Sync')")
            if sync_button:
                logger.info("Found sync button")
                
                # Click sync and watch for progress updates
                await sync_button.click()
                
                # Wait for progress indicator
                progress_indicator = await page.wait_for_selector(
                    "[role='progressbar'], .progress-bar, [data-testid='progress']",
                    timeout=5000
                )
                
                if progress_indicator:
                    logger.info("Progress indicator appeared!")
                    await page.screenshot(path="tests/screenshots/sync_progress.png")
                    logger.info("Screenshot saved: sync_progress.png")
                    
                    # Wait for sync to complete
                    await page.wait_for_selector(
                        "text=Sync completed, text=Sync complete, text=No papers found",
                        timeout=30000
                    )
                    
                    await page.screenshot(path="tests/screenshots/sync_complete.png")
                    logger.info("Screenshot saved: sync_complete.png")
                else:
                    logger.warning("No progress indicator found")
            else:
                logger.warning("No sync button found on page")
                
        except Exception as e:
            logger.error(f"Test failed: {e}")
            await page.screenshot(path="tests/screenshots/error_state.png")
            raise
        finally:
            await browser.close()


async def check_websocket_connection():
    """Check if WebSocket connection works for real-time updates."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: logger.info(f"Browser console: {msg.text}"))
        
        try:
            await page.goto("http://localhost:3000")
            
            # Check for WebSocket errors in console
            await page.wait_for_timeout(3000)
            
            # Evaluate WebSocket status
            ws_status = await page.evaluate("""
                () => {
                    const sockets = Array.from(window.WebSocket.prototype);
                    return {
                        hasWebSocket: typeof WebSocket !== 'undefined',
                        activeConnections: sockets ? sockets.length : 0
                    };
                }
            """)
            
            logger.info(f"WebSocket status: {ws_status}")
            
        except Exception as e:
            logger.error(f"WebSocket check failed: {e}")
        finally:
            await browser.close()


async def main():
    """Run all frontend integration tests."""
    logger.info("Starting frontend integration tests...")
    
    # Create screenshots directory
    import os
    os.makedirs("tests/screenshots", exist_ok=True)
    
    # Test 1: Check WebSocket connection
    logger.info("\n=== Testing WebSocket Connection ===")
    await check_websocket_connection()
    
    # Test 2: Test UI progress bar
    logger.info("\n=== Testing UI Progress Bar ===")
    await test_frontend_progress_bar()
    
    logger.info("\nFrontend integration tests completed!")


if __name__ == "__main__":
    asyncio.run(main())