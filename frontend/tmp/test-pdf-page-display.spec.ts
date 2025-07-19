import { test, expect } from '@playwright/test';

test('Test PDF page information display', async ({ page }) => {
  // Set a longer timeout for this test
  test.setTimeout(60000);
  
  // Navigate to the application
  await page.goto('http://localhost:3000');
  
  // Wait for the app to load
  await page.waitForLoadState('networkidle');
  
  // Navigate to library to see papers
  const libraryLink = page.locator('a:has-text("Library")');
  if (await libraryLink.isVisible()) {
    await libraryLink.click();
    await page.waitForLoadState('networkidle');
    console.log('✅ Navigated to Library');
    
    // Take screenshot of library
    await page.screenshot({ path: 'frontend/tmp/library-page.png', fullPage: true });
    
    // Check if any papers are displayed
    const paperCards = await page.locator('[class*="paper-card"], [class*="border"]').all();
    console.log(`Found ${paperCards.length} papers in library`);
    
    // Look for the paper we reprocessed
    const targetPaper = page.locator('text="Towards Machine Theory of Mind"').first();
    if (await targetPaper.isVisible()) {
      console.log('✅ Found target paper with page info');
      
      // Check if there's a View PDF button
      const viewPdfButton = page.locator('button:has-text("View PDF"), a:has-text("View PDF")').first();
      if (await viewPdfButton.isVisible()) {
        await viewPdfButton.click();
        await page.waitForTimeout(3000);
        
        // Take screenshot of PDF viewer
        await page.screenshot({ path: 'frontend/tmp/pdf-viewer-page-info.png', fullPage: true });
        
        // Check for page information in the PDF viewer
        const pageInfoText = await page.locator('text=/page \\d+/i').allTextContents();
        if (pageInfoText.length > 0) {
          console.log('✅ Page information displayed in PDF viewer:');
          pageInfoText.forEach(text => console.log(`   - ${text}`));
        } else {
          console.log('❌ No page information found in PDF viewer');
        }
      }
    }
  }
  
  // Now test the editor with citations
  const editorLink = page.locator('a:has-text("Editor"), a:has-text("New Document")');
  if (await editorLink.isVisible()) {
    await editorLink.click();
    await page.waitForLoadState('networkidle');
    console.log('✅ Navigated to Editor');
    
    // Find the editor
    await page.waitForTimeout(2000);
    const editor = page.locator('[contenteditable="true"], .editor-container').first();
    
    if (await editor.isVisible()) {
      await editor.click();
      
      // Type text that should trigger citations
      await page.keyboard.type('Recent advances in machine theory of mind demonstrate how language models can understand human behavior through inverse planning approaches.');
      
      // Wait for suggestions
      await page.waitForTimeout(5000);
      
      // Take screenshot
      await page.screenshot({ path: 'frontend/tmp/editor-with-suggestions.png', fullPage: true });
      
      // Check for suggestions
      const suggestions = await page.locator('[class*="suggestion"], [class*="citation"]').all();
      console.log(`Found ${suggestions.length} citation suggestions`);
      
      // Look for View Details button
      const viewDetailsButton = page.locator('button:has-text("View Details")').first();
      if (await viewDetailsButton.isVisible()) {
        console.log('✅ Found View Details button');
        await viewDetailsButton.click();
        await page.waitForTimeout(3000);
        
        // Take screenshot of PDF viewer with citation context
        await page.screenshot({ path: 'frontend/tmp/pdf-viewer-citation-context.png', fullPage: true });
        
        // Check for page information
        const citationPageInfo = await page.locator('text=/citation.*page \\d+/i, text=/found.*page \\d+/i').allTextContents();
        if (citationPageInfo.length > 0) {
          console.log('✅ Citation page information displayed:');
          citationPageInfo.forEach(text => console.log(`   - ${text}`));
        } else {
          console.log('❌ No citation page information found');
        }
      } else {
        console.log('❌ No View Details button found');
      }
    }
  }
});