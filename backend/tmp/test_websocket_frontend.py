"""Test WebSocket functionality in the frontend using Playwright"""
import asyncio
from playwright.async_api import async_playwright
import time
import json

async def test_websocket_frontend():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        
        # Enable console logging
        page = await context.new_page()
        
        # Collect console messages
        console_messages = []
        page.on("console", lambda msg: console_messages.append({
            "type": msg.type,
            "text": msg.text,
            "time": time.strftime("%H:%M:%S")
        }))
        
        # Navigate to the application
        print("1. Navigating to http://localhost:3000...")
        await page.goto("http://localhost:3000")
        await page.wait_for_timeout(2000)  # Wait for initial load
        
        # Click on Try Demo button to get to the editor
        try_demo_button = page.locator('button:has-text("Try Demo")')
        if await try_demo_button.count() > 0:
            print("   - Clicking 'Try Demo' button...")
            await try_demo_button.click()
            await page.wait_for_timeout(3000)  # Wait for editor to load
        
        # Take a screenshot of the initial state
        await page.screenshot(path="tmp/test_initial_state.png")
        print("   - Screenshot saved: tmp/test_initial_state.png")
        
        # Clear console messages from initial load
        initial_console = console_messages.copy()
        console_messages.clear()
        
        print("\n2. Initial console messages:")
        for msg in initial_console[-10:]:  # Show last 10 messages
            print(f"   [{msg['time']}] {msg['type']}: {msg['text'][:100]}...")
        
        # Check for WebSocket connection logs
        ws_logs = [msg for msg in initial_console if "websocket" in msg['text'].lower() or "ws://" in msg['text'].lower()]
        print(f"\n3. WebSocket-related logs found: {len(ws_logs)}")
        for msg in ws_logs:
            print(f"   - {msg['text'][:200]}...")
        
        # Click on the editor to focus it
        print("\n4. Focusing on the editor...")
        # Try multiple selectors for the editor
        editor_selectors = [
            '[data-lexical-editor="true"]',
            '.lexical-editor',
            '[contenteditable="true"]',
            '.editor-container [contenteditable]'
        ]
        
        editor = None
        for selector in editor_selectors:
            if await page.locator(selector).count() > 0:
                editor = page.locator(selector).first
                print(f"   - Found editor with selector: {selector}")
                break
        
        if editor:
            await editor.click()
            await page.wait_for_timeout(1000)
        else:
            print("   - WARNING: Could not find editor element!")
        
        # Type some text to trigger suggestions
        print("\n5. Typing text to trigger suggestions...")
        test_text = "Machine learning has revolutionized many fields including "
        await page.keyboard.type(test_text, delay=50)
        await page.wait_for_timeout(2000)  # Wait for suggestions
        
        # Take screenshot after typing
        await page.screenshot(path="tmp/test_after_typing.png")
        print("   - Screenshot saved: tmp/test_after_typing.png")
        
        # Check console for WebSocket activity
        print("\n6. Console messages after typing:")
        for msg in console_messages[-10:]:
            print(f"   [{msg['time']}] {msg['type']}: {msg['text'][:100]}...")
        
        # Check if suggestions appeared
        suggestions = await page.locator('.citation-suggestion-item').count()
        print(f"\n7. Citation suggestions found: {suggestions}")
        
        if suggestions > 0:
            # Take screenshot of suggestions
            await page.screenshot(path="tmp/test_suggestions.png")
            print("   - Screenshot saved: tmp/test_suggestions.png")
            
            # Get suggestion text
            for i in range(min(3, suggestions)):
                suggestion = await page.locator('.citation-suggestion-item').nth(i)
                title = await suggestion.locator('.font-medium').text_content()
                print(f"   - Suggestion {i+1}: {title}")
        
        # Test enhanced mode toggle
        print("\n8. Testing enhanced mode toggle...")
        settings_button = page.locator('button:has-text("Settings")')
        if await settings_button.count() > 0:
            await settings_button.click()
            await page.wait_for_timeout(500)
            
            # Toggle enhanced mode
            enhanced_toggle = await page.locator('text="Use Enhanced Mode"').locator('..//button[role="switch"]')
            if await enhanced_toggle.count() > 0:
                await enhanced_toggle.click()
                await page.wait_for_timeout(500)
                print("   - Toggled enhanced mode")
                
                # Close settings
                close_button = await page.locator('button[aria-label="Close"]')
                if await close_button.count() > 0:
                    await close_button.click()
                else:
                    await page.keyboard.press('Escape')
                await page.wait_for_timeout(500)
        
        # Type more text to test after toggle
        print("\n9. Testing after mode toggle...")
        await page.keyboard.type(" natural language processing", delay=50)
        await page.wait_for_timeout(2000)
        
        # Final screenshot
        await page.screenshot(path="tmp/test_final_state.png")
        print("   - Screenshot saved: tmp/test_final_state.png")
        
        # Check for any errors
        error_logs = [msg for msg in console_messages if msg['type'] == 'error']
        print(f"\n10. Error messages found: {len(error_logs)}")
        for msg in error_logs:
            print(f"    - ERROR: {msg['text']}")
        
        # Check for infinite loop indicators
        ws_reconnect_logs = [msg for msg in console_messages if "reconnect" in msg['text'].lower() or "retry" in msg['text'].lower()]
        print(f"\n11. Reconnection attempts found: {len(ws_reconnect_logs)}")
        if len(ws_reconnect_logs) > 5:
            print("    ⚠️  WARNING: Multiple reconnection attempts detected - possible infinite loop!")
        
        # Summary
        print("\n12. Test Summary:")
        print(f"    - Total console messages: {len(console_messages)}")
        print(f"    - Errors: {len(error_logs)}")
        print(f"    - WebSocket logs: {len(ws_logs)}")
        print(f"    - Suggestions displayed: {suggestions}")
        print(f"    - Reconnection attempts: {len(ws_reconnect_logs)}")
        
        # Keep browser open for manual inspection
        print("\n13. Browser will remain open for 10 seconds for manual inspection...")
        await page.wait_for_timeout(10000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_websocket_frontend())