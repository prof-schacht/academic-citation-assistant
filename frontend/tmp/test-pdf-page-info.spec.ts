import { test, expect } from '@playwright/test';

test('Check PDF page information display', async ({ page }) => {
  // Navigate to the application
  await page.goto('http://localhost:3000');
  
  // Wait for the page to load
  await page.waitForLoadState('networkidle');
  
  // Take a screenshot of the current state
  await page.screenshot({ path: 'frontend/tmp/screenshot-initial.png', fullPage: true });
  
  // Check if we're on the editor page or need to navigate
  const editorButton = page.locator('text="New Document"');
  if (await editorButton.isVisible()) {
    await editorButton.click();
    await page.waitForLoadState('networkidle');
  }
  
  // Take screenshot of editor
  await page.screenshot({ path: 'frontend/tmp/screenshot-editor.png', fullPage: true });
  
  // Type some text to trigger citation suggestions
  const editor = page.locator('[contenteditable="true"]').first();
  await editor.click();
  await editor.fill('Recent advances in machine learning have shown that transformer models can achieve state-of-the-art results in various NLP tasks.');
  
  // Wait for suggestions
  await page.waitForTimeout(3000);
  
  // Take screenshot with suggestions
  await page.screenshot({ path: 'frontend/tmp/screenshot-suggestions.png', fullPage: true });
  
  // Check if any suggestions have page information
  const suggestions = await page.locator('[data-testid="citation-suggestion"]').all();
  console.log(`Found ${suggestions.length} suggestions`);
  
  // Look for the first suggestion with a "View Details" button
  const viewDetailsButton = page.locator('button:has-text("View Details")').first();
  if (await viewDetailsButton.isVisible()) {
    // Click to view details
    await viewDetailsButton.click();
    await page.waitForTimeout(2000);
    
    // Take screenshot of PDF viewer
    await page.screenshot({ path: 'frontend/tmp/screenshot-pdf-viewer.png', fullPage: true });
    
    // Check if page information is displayed
    const pageInfo = page.locator('text=/page \\d+/i');
    if (await pageInfo.isVisible()) {
      console.log('✅ Page information is displayed!');
      const pageText = await pageInfo.textContent();
      console.log(`Page info: ${pageText}`);
    } else {
      console.log('❌ No page information found');
    }
  } else {
    console.log('No View Details button found - checking library');
    
    // Navigate to library
    const libraryLink = page.locator('a[href="/library"]');
    if (await libraryLink.isVisible()) {
      await libraryLink.click();
      await page.waitForLoadState('networkidle');
      await page.screenshot({ path: 'frontend/tmp/screenshot-library.png', fullPage: true });
    }
  }
});