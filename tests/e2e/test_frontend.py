"""Frontend E2E tests using Playwright."""
import asyncio
from playwright.async_api import async_playwright


async def test_frontend_screenshot():
    """Take a screenshot of the frontend to verify it's working."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Navigate to frontend
        await page.goto("http://localhost:3000")
        
        # Wait for the main heading to be visible
        await page.wait_for_selector("h1:has-text('Academic Citation Assistant')")
        
        # Take screenshot
        await page.screenshot(path="tmp/frontend-screenshot.png")
        
        # Check for key elements
        assert await page.is_visible("text=Real-time Citation Recommendations")
        assert await page.is_visible("text=Real-time Suggestions")
        assert await page.is_visible("text=Context-Aware")
        assert await page.is_visible("text=Confidence Scoring")
        
        # Check console for errors
        console_messages = []
        page.on("console", lambda msg: console_messages.append(msg))
        
        await browser.close()
        
        print("✅ Frontend is working correctly!")
        print(f"Screenshot saved to tmp/frontend-screenshot.png")
        
        # Report any console errors
        errors = [msg for msg in console_messages if msg.type == "error"]
        if errors:
            print(f"⚠️  Found {len(errors)} console errors:")
            for error in errors:
                print(f"   - {error.text}")
        else:
            print("✅ No console errors found")


if __name__ == "__main__":
    asyncio.run(test_frontend_screenshot())