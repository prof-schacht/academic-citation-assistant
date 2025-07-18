import { test, expect } from '@playwright/test';

test.describe('PDF Viewer Feature Test on Port 3001', () => {
  test('should test PDF viewer functionality', async ({ page }) => {
    // Set up console monitoring
    const consoleMessages: { type: string, text: string }[] = [];
    page.on('console', msg => {
      consoleMessages.push({ type: msg.type(), text: msg.text() });
    });
    
    // Navigate to the application on port 3001
    await page.goto('http://localhost:3001');
    
    // Wait for the page to load
    await page.waitForTimeout(3000);
    
    // Take screenshot of initial state
    await page.screenshot({ path: 'tmp/screenshots/port3001-01-initial.png', fullPage: true });
    
    // Check if the app loaded properly
    const appRoot = page.locator('#root');
    const hasContent = await appRoot.textContent();
    console.log('App has content:', !!hasContent);
    
    // Look for main navigation or header
    const header = page.locator('header, nav, [class*="header"], [class*="navbar"]');
    if (await header.isVisible()) {
      console.log('Header/Navigation found');
      await page.screenshot({ path: 'tmp/screenshots/port3001-02-header.png' });
    }
    
    // Try to find and click on a document
    const documentLinks = page.locator('a[href*="/document"], button:has-text("Document"), .document-item');
    const documentCount = await documentLinks.count();
    console.log('Document links found:', documentCount);
    
    if (documentCount > 0) {
      await documentLinks.first().click();
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'tmp/screenshots/port3001-03-document.png', fullPage: true });
    }
    
    // Check current URL
    const currentUrl = page.url();
    console.log('Current URL:', currentUrl);
    
    // If not on a document page, navigate directly
    if (!currentUrl.includes('/document/')) {
      // Try to navigate to a document directly
      await page.goto('http://localhost:3001/document/1');
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'tmp/screenshots/port3001-04-direct-nav.png', fullPage: true });
    }
    
    // Look for the editor
    const editor = page.locator('[contenteditable="true"], .editor-content, [role="textbox"]');
    const editorVisible = await editor.isVisible();
    console.log('Editor visible:', editorVisible);
    
    if (editorVisible) {
      // Clear and type content
      await editor.click();
      await page.keyboard.press('Control+A');
      await page.keyboard.type('Transformer models like BERT have shown remarkable success in NLP tasks.');
      await page.waitForTimeout(3000);
      await page.screenshot({ path: 'tmp/screenshots/port3001-05-typed.png', fullPage: true });
      
      // Look for citations panel
      const citationsPanel = page.locator('.citations-panel, aside:has-text("Citations"), [class*="citation"]');
      const citationsPanelVisible = await citationsPanel.isVisible();
      console.log('Citations panel visible:', citationsPanelVisible);
      
      // Look for citation suggestions
      const suggestions = page.locator('.citation-suggestion, .citation-card, [class*="suggestion"]');
      const suggestionCount = await suggestions.count();
      console.log('Citation suggestions found:', suggestionCount);
      
      // Find View Details button
      const viewDetailsBtn = page.locator('button:has-text("View Details"), button:has-text("View PDF")').first();
      if (await viewDetailsBtn.isVisible()) {
        console.log('View Details button found');
        
        // Check layout before click
        const mainColumns = await page.locator('main > div > div').count();
        console.log('Columns before click:', mainColumns);
        
        // Click View Details
        await viewDetailsBtn.click();
        await page.waitForTimeout(2000);
        await page.screenshot({ path: 'tmp/screenshots/port3001-06-pdf-viewer.png', fullPage: true });
        
        // Check if PDF viewer appeared
        const pdfViewer = page.locator('.pdf-viewer, [class*="PdfViewer"], iframe, .viewer-container');
        const pdfVisible = await pdfViewer.isVisible();
        console.log('PDF viewer visible:', pdfVisible);
        
        // Check layout after click
        const columnsAfter = await page.locator('main > div > div').count();
        console.log('Columns after click:', columnsAfter);
        
        // Look for close button
        const closeBtn = page.locator('button[title*="Close"], button svg[stroke="currentColor"]').last();
        if (await closeBtn.isVisible()) {
          await closeBtn.click();
          await page.waitForTimeout(1000);
          console.log('Clicked close button');
        }
      }
    }
    
    // Print console messages
    console.log('\n=== Console Messages ===');
    consoleMessages.forEach(msg => {
      if (msg.type === 'error') {
        console.log(`ERROR: ${msg.text}`);
      } else if (msg.type === 'warning') {
        console.log(`WARNING: ${msg.text}`);
      }
    });
    
    // Final screenshot
    await page.screenshot({ path: 'tmp/screenshots/port3001-07-final.png', fullPage: true });
  });
});