import { test, expect } from '@playwright/test';

test.describe('Citation Insertion Save', () => {
  test('should save document immediately after citation insertion', async ({ page }) => {
    // Navigate to documents page
    await page.goto('http://localhost:3000/documents');
    
    // Create a new document
    await page.click('button:has-text("Create New Document")');
    
    // Wait for editor to load
    await page.waitForSelector('.lexical-editor');
    
    // Type some text
    await page.click('.lexical-editor');
    await page.keyboard.type('This is a test sentence about machine learning');
    
    // Wait for citation suggestions
    await page.waitForSelector('.citation-suggestion', { timeout: 10000 });
    
    // Click the first citation suggestion
    await page.click('.citation-suggestion >> nth=0');
    
    // Immediately click on Bibliography tab
    await page.click('button:has-text("Bibliography")');
    
    // Wait a moment for save to complete
    await page.waitForTimeout(2000);
    
    // Click back to Editor tab
    await page.click('button:has-text("Editor")');
    
    // Verify the text is still there
    const editorContent = await page.textContent('.lexical-editor');
    expect(editorContent).toContain('This is a test sentence about machine learning');
    
    // Verify citation is present (as a citation node)
    const citationNode = await page.locator('.citation-node').count();
    expect(citationNode).toBeGreaterThan(0);
  });

  test('should show inserted citations in Citations tab', async ({ page }) => {
    // Navigate to documents page
    await page.goto('http://localhost:3000/documents');
    
    // Create a new document
    await page.click('button:has-text("Create New Document")');
    
    // Wait for editor to load
    await page.waitForSelector('.lexical-editor');
    
    // Type some text
    await page.click('.lexical-editor');
    await page.keyboard.type('Research on neural networks shows promising results');
    
    // Wait for citation suggestions
    await page.waitForSelector('.citation-suggestion', { timeout: 10000 });
    
    // Click the first citation suggestion
    await page.click('.citation-suggestion >> nth=0');
    
    // Click on Citations tab
    await page.click('button:has-text("Citations")');
    
    // Check for "Citations in Document" section
    await page.waitForSelector('h3:has-text("Citations in Document")');
    
    // Verify the citation is listed
    const citationInDocument = await page.locator('.bg-gray-50 >> text=Added to bibliography ✓').count();
    expect(citationInDocument).toBeGreaterThan(0);
  });

  test('should auto-add citations to bibliography', async ({ page }) => {
    // Navigate to documents page
    await page.goto('http://localhost:3000/documents');
    
    // Create a new document
    await page.click('button:has-text("Create New Document")');
    
    // Wait for editor to load
    await page.waitForSelector('.lexical-editor');
    
    // Type some text
    await page.click('.lexical-editor');
    await page.keyboard.type('Deep learning techniques are revolutionizing AI');
    
    // Wait for citation suggestions
    await page.waitForSelector('.citation-suggestion', { timeout: 10000 });
    
    // Click the first citation suggestion
    await page.click('.citation-suggestion >> nth=0');
    
    // Click on Bibliography tab
    await page.click('button:has-text("Bibliography")');
    
    // Wait for papers to load
    await page.waitForSelector('.paper-card, [data-testid="paper-item"]', { timeout: 5000 });
    
    // Verify at least one paper is in the bibliography
    const paperCount = await page.locator('.paper-card, [data-testid="paper-item"]').count();
    expect(paperCount).toBeGreaterThan(0);
  });
});