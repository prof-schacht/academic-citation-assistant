import { test, expect } from '@playwright/test';

test.describe('PDF Viewer Feature - Manual Test', () => {
  test('should manually test PDF viewer functionality', async ({ page }) => {
    // Set up console monitoring
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Navigate to the application
    await page.goto('http://localhost:3000');
    
    // Wait for the page to load
    await page.waitForTimeout(3000);
    
    // Take screenshot of current state
    await page.screenshot({ path: 'tmp/screenshots/manual-01-initial.png', fullPage: true });
    
    // Try to find any existing documents in the list
    const documentItems = page.locator('.document-item, [class*="document"], .list-item');
    const documentCount = await documentItems.count();
    console.log('Found documents:', documentCount);
    
    if (documentCount > 0) {
      // Click the first document
      await documentItems.first().click();
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'tmp/screenshots/manual-02-document-opened.png', fullPage: true });
    }
    
    // Check for editor and type content
    const editor = page.locator('[contenteditable="true"], .editor, [class*="editor"]');
    const editorExists = await editor.isVisible();
    console.log('Editor visible:', editorExists);
    
    if (editorExists) {
      await editor.click();
      await page.keyboard.press('Control+A'); // Select all
      await page.keyboard.press('Delete'); // Clear content
      
      // Type content that should trigger citations
      await editor.type('The transformer architecture introduced by Vaswani et al. (2017) has revolutionized natural language processing. BERT (Devlin et al., 2018) and GPT models have shown remarkable performance.');
      
      await page.waitForTimeout(3000); // Wait for citations to load
      await page.screenshot({ path: 'tmp/screenshots/manual-03-typed-content.png', fullPage: true });
    }
    
    // Look for citation suggestions in various possible containers
    const citationSelectors = [
      '.citation-suggestion',
      '.citation-card', 
      '[class*="citation"]',
      '.suggestions',
      '.citation-item',
      'button:has-text("View Details")'
    ];
    
    let citationsFound = false;
    for (const selector of citationSelectors) {
      const elements = page.locator(selector);
      const count = await elements.count();
      if (count > 0) {
        console.log(`Found ${count} elements with selector: ${selector}`);
        citationsFound = true;
        
        // Try to find View Details button
        const viewDetailsBtn = elements.locator('button:has-text("View Details")').first();
        if (await viewDetailsBtn.isVisible()) {
          console.log('Found View Details button');
          
          // Get the layout before clicking
          const columnsBefore = await page.locator('.flex > div, .grid > div, [class*="col-"]').count();
          console.log('Columns before clicking View Details:', columnsBefore);
          
          // Click View Details
          await viewDetailsBtn.click();
          await page.waitForTimeout(2000);
          
          await page.screenshot({ path: 'tmp/screenshots/manual-04-view-details-clicked.png', fullPage: true });
          
          // Check for PDF viewer
          const pdfViewerSelectors = [
            '.pdf-viewer',
            '[class*="pdf"]',
            'iframe',
            '.viewer-container',
            '[class*="PdfViewer"]'
          ];
          
          for (const pdfSelector of pdfViewerSelectors) {
            const pdfElement = page.locator(pdfSelector);
            if (await pdfElement.isVisible()) {
              console.log(`PDF viewer found with selector: ${pdfSelector}`);
              break;
            }
          }
          
          // Check columns after
          const columnsAfter = await page.locator('.flex > div, .grid > div, [class*="col-"]').count();
          console.log('Columns after clicking View Details:', columnsAfter);
          
          // Look for close button
          const closeBtn = page.locator('button[title*="Close"], button[aria-label*="close"], svg').last();
          if (await closeBtn.isVisible()) {
            await closeBtn.click();
            await page.waitForTimeout(1000);
            await page.screenshot({ path: 'tmp/screenshots/manual-05-after-close.png', fullPage: true });
          }
          
          break;
        }
      }
    }
    
    if (!citationsFound) {
      console.log('No citation suggestions found');
      
      // Take screenshot to see what's on the page
      await page.screenshot({ path: 'tmp/screenshots/manual-no-citations.png', fullPage: true });
    }
    
    // Report console errors
    if (consoleErrors.length > 0) {
      console.log('\n=== Console Errors ===');
      consoleErrors.forEach(err => console.log(err));
    } else {
      console.log('\nNo console errors detected');
    }
    
    // Get page structure for debugging
    const bodyHTML = await page.locator('body').innerHTML();
    console.log('\n=== Page has the following main elements ===');
    const mainElements = await page.locator('main, [role="main"], .app, #app, #root > div > div').allTextContents();
    console.log('Main content areas found:', mainElements.length);
  });
});