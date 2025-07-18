import { test, expect } from '@playwright/test';

test.describe('PDF Viewer Feature Final Test', () => {
  test('should test PDF viewer three-column layout', async ({ page }) => {
    // Set up console monitoring
    const consoleMessages: { type: string, text: string }[] = [];
    page.on('console', msg => {
      consoleMessages.push({ type: msg.type(), text: msg.text() });
    });
    
    // Navigate to the application on port 3001
    await page.goto('http://localhost:3001');
    await page.waitForTimeout(2000);
    
    // Take initial screenshot
    await page.screenshot({ path: 'tmp/screenshots/final-01-home.png', fullPage: true });
    
    // Click on "Get Started" or navigate to documents
    const getStartedBtn = page.locator('a:has-text("Get Started"), button:has-text("Get Started")');
    if (await getStartedBtn.isVisible()) {
      await getStartedBtn.click();
      await page.waitForTimeout(1000);
    }
    
    // Look for existing documents or create new
    const documentList = page.locator('.document-list, .documents-container, [class*="document"]');
    await page.screenshot({ path: 'tmp/screenshots/final-02-documents.png', fullPage: true });
    
    // Try to open the first document or create a new one
    const firstDoc = page.locator('.document-item, a[href*="/document/"]').first();
    if (await firstDoc.isVisible()) {
      await firstDoc.click();
    } else {
      // Try to create a new document
      const newDocBtn = page.locator('button:has-text("New Document"), button:has-text("Create")').first();
      if (await newDocBtn.isVisible()) {
        await newDocBtn.click();
      }
    }
    
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'tmp/screenshots/final-03-editor.png', fullPage: true });
    
    // Find the editor and type content
    const editor = page.locator('[contenteditable="true"]').first();
    if (await editor.isVisible()) {
      console.log('Editor found, typing content...');
      await editor.click();
      
      // Clear any existing content
      await page.keyboard.press('Control+A');
      await page.keyboard.press('Delete');
      
      // Type content that should trigger citations
      await editor.type('Recent advances in deep learning have been driven by transformer architectures. BERT and GPT models have shown state-of-the-art performance on various NLP tasks. The attention mechanism introduced by Vaswani et al. has become fundamental.');
      
      // Wait for citations to load
      await page.waitForTimeout(3000);
      await page.screenshot({ path: 'tmp/screenshots/final-04-with-text.png', fullPage: true });
      
      // Check if citations panel is visible
      const citationsVisible = await page.locator('text=Citations').isVisible();
      console.log('Citations panel visible:', citationsVisible);
      
      // Count initial columns
      const initialColumns = await page.locator('main > div > div > div').count();
      console.log('Initial number of main content columns:', initialColumns);
      
      // Look for View Details buttons
      const viewDetailsButtons = page.locator('button:has-text("View Details")');
      const buttonCount = await viewDetailsButtons.count();
      console.log('View Details buttons found:', buttonCount);
      
      if (buttonCount > 0) {
        // Get info about the citation before clicking
        const citationCard = viewDetailsButtons.first().locator('..').locator('..');
        const citationTitle = await citationCard.locator('h3, .title, [class*="title"]').textContent();
        console.log('Clicking View Details for:', citationTitle);
        
        // Click the first View Details button
        await viewDetailsButtons.first().click();
        await page.waitForTimeout(2000);
        
        // Take screenshot after clicking
        await page.screenshot({ path: 'tmp/screenshots/final-05-pdf-viewer-open.png', fullPage: true });
        
        // Check if PDF viewer appeared
        const pdfViewerSelectors = [
          '.pdf-viewer',
          '[class*="PdfViewer"]',
          'div:has(> iframe)',
          '.viewer-container',
          'div:has-text("Loading PDF")',
          'div:has-text("No PDF available")'
        ];
        
        let pdfViewerFound = false;
        for (const selector of pdfViewerSelectors) {
          const element = page.locator(selector).first();
          if (await element.isVisible()) {
            console.log(`PDF viewer found with selector: ${selector}`);
            pdfViewerFound = true;
            break;
          }
        }
        
        // Count columns after opening PDF viewer
        const columnsAfter = await page.locator('main > div > div > div').count();
        console.log('Number of columns after opening PDF viewer:', columnsAfter);
        
        // Check if the layout is three columns
        const threeColumnLayout = await page.locator('.flex > div').count();
        console.log('Flex container children count:', threeColumnLayout);
        
        // Check if citation is highlighted
        const highlightedCitation = await page.locator('.citation-card.selected, .selected, [class*="active"], [class*="highlighted"]').count();
        console.log('Highlighted citations found:', highlightedCitation);
        
        // Look for close button
        const closeButton = page.locator('button[title*="Close"], button:has(svg path[d*="M6 18L18 6M6 6l12 12"])');
        if (await closeButton.isVisible()) {
          console.log('Close button found');
          await closeButton.click();
          await page.waitForTimeout(1000);
          
          // Check if PDF viewer is hidden
          await page.screenshot({ path: 'tmp/screenshots/final-06-pdf-closed.png', fullPage: true });
          const columnsAfterClose = await page.locator('main > div > div > div').count();
          console.log('Columns after closing PDF viewer:', columnsAfterClose);
        }
        
        // Summary
        console.log('\n=== PDF Viewer Test Summary ===');
        console.log('PDF viewer found:', pdfViewerFound);
        console.log('Column transition:', `${initialColumns} -> ${columnsAfter} -> ${columnsAfterClose || columnsAfter}`);
        console.log('Three-column layout achieved:', columnsAfter >= 3);
      } else {
        console.log('No View Details buttons found - citations may not have loaded');
      }
    } else {
      console.log('Editor not found');
    }
    
    // Print console errors
    const errors = consoleMessages.filter(m => m.type === 'error');
    if (errors.length > 0) {
      console.log('\n=== Console Errors ===');
      errors.forEach(err => console.log(err.text));
    }
  });
});