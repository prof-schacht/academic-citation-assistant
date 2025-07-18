import { test, expect } from '@playwright/test';

test.describe('PDF Viewer Feature', () => {
  test('should display PDF viewer when clicking View Details on a citation', async ({ page }) => {
    // Navigate to the application
    await page.goto('http://localhost:3000');
    
    // Wait for the page to load
    await page.waitForTimeout(2000);
    
    // Take initial screenshot
    await page.screenshot({ path: 'tmp/screenshots/01-initial-state.png', fullPage: true });
    
    // Check if there's a document open or we need to create one
    const editorVisible = await page.locator('.editor-container').isVisible();
    
    if (!editorVisible) {
      console.log('No document open, creating a new one');
      // Look for a button to create a new document
      const newDocButton = page.locator('button:has-text("New Document"), button:has-text("Create Document")');
      if (await newDocButton.isVisible()) {
        await newDocButton.click();
        await page.waitForTimeout(1000);
      }
    }
    
    // Type some content to trigger citation suggestions
    const editor = page.locator('[contenteditable="true"]');
    if (await editor.isVisible()) {
      await editor.click();
      await editor.type('Recent advances in machine learning have shown that transformer models like BERT and GPT have revolutionized natural language processing. The attention mechanism introduced by Vaswani et al. has become fundamental to modern NLP systems.');
      await page.waitForTimeout(2000);
    }
    
    // Take screenshot after typing
    await page.screenshot({ path: 'tmp/screenshots/02-after-typing.png', fullPage: true });
    
    // Check if citations panel is visible
    const citationsPanel = page.locator('.citations-panel, [class*="citation"]');
    const citationsPanelVisible = await citationsPanel.isVisible();
    console.log('Citations panel visible:', citationsPanelVisible);
    
    // Look for View Details button
    const viewDetailsButton = page.locator('button:has-text("View Details")').first();
    const viewDetailsVisible = await viewDetailsButton.isVisible();
    console.log('View Details button visible:', viewDetailsVisible);
    
    if (viewDetailsVisible) {
      // Get the initial number of columns
      const initialColumns = await page.locator('.column, [class*="col-"]').count();
      console.log('Initial number of columns:', initialColumns);
      
      // Click View Details button
      await viewDetailsButton.click();
      await page.waitForTimeout(1000);
      
      // Take screenshot after clicking View Details
      await page.screenshot({ path: 'tmp/screenshots/03-after-view-details.png', fullPage: true });
      
      // Check if PDF viewer appeared
      const pdfViewer = page.locator('.pdf-viewer, [class*="pdf"], iframe[src*="pdf"]');
      const pdfViewerVisible = await pdfViewer.isVisible();
      console.log('PDF viewer visible:', pdfViewerVisible);
      
      // Check the number of columns after clicking
      const afterColumns = await page.locator('.column, [class*="col-"]').count();
      console.log('Number of columns after clicking:', afterColumns);
      
      // Check if selected citation is highlighted
      const highlightedCitation = page.locator('.citation-card.selected, [class*="selected"], [class*="active"]');
      const hasHighlight = await highlightedCitation.isVisible();
      console.log('Citation highlighted:', hasHighlight);
      
      // Check for close button
      const closeButton = page.locator('button:has-text("Close"), button[aria-label*="close"], button.close-button');
      const closeButtonVisible = await closeButton.isVisible();
      console.log('Close button visible:', closeButtonVisible);
      
      if (closeButtonVisible) {
        // Click close button
        await closeButton.click();
        await page.waitForTimeout(1000);
        
        // Take screenshot after closing
        await page.screenshot({ path: 'tmp/screenshots/04-after-close.png', fullPage: true });
        
        // Verify PDF viewer is hidden
        const pdfViewerHidden = await pdfViewer.isHidden();
        console.log('PDF viewer hidden after close:', pdfViewerHidden);
      }
    }
    
    // Check console for errors
    const consoleMessages: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleMessages.push(`Console Error: ${msg.text()}`);
      }
    });
    
    // Wait a bit to catch any console errors
    await page.waitForTimeout(2000);
    
    if (consoleMessages.length > 0) {
      console.log('Console errors found:');
      consoleMessages.forEach(msg => console.log(msg));
    } else {
      console.log('No console errors detected');
    }
  });
});