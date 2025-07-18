"""Debug script to check documents page and console errors."""
from playwright.sync_api import sync_playwright
import time

def debug_documents_page():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Listen for console messages
        console_messages = []
        page.on("console", lambda msg: console_messages.append({
            'type': msg.type,
            'text': msg.text,
            'location': msg.location
        }))
        
        # Listen for page errors
        page_errors = []
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        
        # Navigate to documents page
        print("Navigating to documents page...")
        page.goto('http://localhost:5173/documents', wait_until='networkidle')
        
        # Take screenshot
        page.screenshot(path="tmp/documents_page_screenshot.png")
        print("Screenshot saved to tmp/documents_page_screenshot.png")
        
        # Print console messages
        print("\n=== Console Messages ===")
        for msg in console_messages:
            print(f"{msg['type']}: {msg['text']}")
            if msg['location']:
                print(f"  at {msg['location']}")
        
        # Print page errors
        print("\n=== Page Errors ===")
        for error in page_errors:
            print(error)
        
        # Check network requests
        print("\n=== Checking API calls ===")
        
        # Wait a bit for any pending requests
        time.sleep(2)
        
        # Close browser
        browser.close()

if __name__ == "__main__":
    debug_documents_page()