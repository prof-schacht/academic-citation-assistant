import { test, expect } from '@playwright/test';

test.describe('Citation Insertion and Save Behavior', () => {
  test.beforeEach(async ({ page }) => {
    // Set up auth token
    await page.context().addCookies([{
      name: 'authToken',
      value: 'dummy-auth-token-for-testing',
      domain: 'localhost',
      path: '/',
    }]);
    
    // Mock API responses
    await page.route('**/api/users/profile', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user_id: 'test-user-id',
          email: 'test@example.com',
          name: 'Test User',
          created_at: new Date().toISOString(),
        }),
      });
    });

    // Mock document creation/loading
    await page.route('**/api/documents', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'test-doc-123',
            title: 'Test Document',
            content: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }),
        });
      }
    });

    await page.route('**/api/documents/test-doc-123', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'test-doc-123',
          title: 'Test Document',
          content: null,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }),
      });
    });

    // Navigate to editor
    await page.goto('http://localhost:5173/editor/test-doc-123');
    await page.waitForLoadState('networkidle');
  });

  test('should observe editor state changes and save behavior after citation insertion', async ({ page }) => {
    // Wait for editor to be ready
    await page.waitForSelector('[contenteditable="true"]', { timeout: 10000 });
    
    // Type some initial text
    const editor = page.locator('[contenteditable="true"]');
    await editor.click();
    await editor.type('This is a test sentence that needs a citation.');
    
    // Take a screenshot of initial state
    await page.screenshot({ path: 'tests/screenshots/before-citation.png', fullPage: true });
    
    // Wait a bit to see if auto-save triggers
    await page.waitForTimeout(3000);
    
    // Check if saving indicator appears
    const savingIndicator = page.locator('text=/saving/i');
    const savedIndicator = page.locator('text=/saved/i');
    
    // Log console messages
    page.on('console', msg => {
      console.log(`Browser console: ${msg.type()}: ${msg.text()}`);
    });
    
    // Mock citation suggestions
    await page.route('**/api/papers/suggest**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          suggestions: [{
            paperId: 'test-paper-1',
            title: 'Test Paper Title',
            authors: ['Author One', 'Author Two'],
            year: 2023,
            confidence: 0.95,
            abstract: 'Test abstract',
          }],
        }),
      });
    });
    
    // Click on Citations tab to see suggestions
    await page.click('button:has-text("Citations")');
    await page.waitForTimeout(1000);
    
    // Click back to editor
    await page.click('button:has-text("Editor")');
    
    // Insert a citation using the panel
    await page.click('button:has-text("Insert")');
    
    // Take a screenshot after citation insertion
    await page.screenshot({ path: 'tests/screenshots/after-citation.png', fullPage: true });
    
    // Wait to see if save triggers
    await page.waitForTimeout(3000);
    
    // Type more text after citation
    await editor.click();
    await page.keyboard.press('End'); // Go to end of line
    await editor.type(' This text is after the citation.');
    
    // Take a screenshot after additional text
    await page.screenshot({ path: 'tests/screenshots/after-more-text.png', fullPage: true });
    
    // Wait and check save status
    await page.waitForTimeout(3000);
    
    // Check if the editor still has focus
    const isFocused = await editor.evaluate((el) => el === document.activeElement);
    console.log('Editor focused after citation insertion:', isFocused);
    
    // Get editor content
    const editorContent = await editor.textContent();
    console.log('Editor content:', editorContent);
    
    // Check for any error messages
    const errorMessages = await page.locator('.error, [role="alert"]').allTextContents();
    if (errorMessages.length > 0) {
      console.log('Error messages found:', errorMessages);
    }
    
    // Log network activity
    const requests: string[] = [];
    page.on('request', request => {
      if (request.url().includes('/api/documents')) {
        requests.push(`${request.method()} ${request.url()}`);
      }
    });
    
    // Wait a bit more to capture any delayed saves
    await page.waitForTimeout(2000);
    console.log('Document API requests:', requests);
  });

  test('should check if onChange events fire after citation insertion', async ({ page }) => {
    // Inject a script to monitor onChange events
    await page.addScriptTag({
      content: `
        window.onChangeEvents = [];
        const originalConsoleLog = console.log;
        console.log = function(...args) {
          originalConsoleLog(...args);
          if (args[0] && args[0].includes && (args[0].includes('onChange') || args[0].includes('save'))) {
            window.onChangeEvents.push(args.join(' '));
          }
        };
      `
    });
    
    // Wait for editor
    await page.waitForSelector('[contenteditable="true"]');
    const editor = page.locator('[contenteditable="true"]');
    
    // Type text
    await editor.click();
    await editor.type('Text before citation.');
    
    // Wait and clear events
    await page.waitForTimeout(1000);
    await page.evaluate(() => { window.onChangeEvents = []; });
    
    // Simulate citation insertion
    await page.evaluate(() => {
      // This simulates what happens when a citation is inserted
      const event = new Event('input', { bubbles: true });
      document.querySelector('[contenteditable="true"]')?.dispatchEvent(event);
    });
    
    // Check events
    await page.waitForTimeout(1000);
    const events = await page.evaluate(() => window.onChangeEvents);
    console.log('onChange events after citation:', events);
  });
});