import { chromium } from '@playwright/test';

async function testFrontend() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    console.log('1. Navigating to frontend...');
    await page.goto('http://localhost:3002');
    
    // Take screenshot of homepage
    await page.screenshot({ path: 'test-homepage.png' });
    console.log('✓ Homepage loaded');
    
    // Check if page loads without errors
    await page.waitForTimeout(2000);
    
    // Check console for errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.error('Console error:', msg.text());
      }
    });
    
    // Try to navigate to documents
    console.log('2. Navigating to documents...');
    await page.click('text=My Documents');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'test-documents.png' });
    console.log('✓ Documents page loaded');
    
    // Try to navigate to library
    console.log('3. Navigating to paper library...');
    await page.click('text=Paper Library');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'test-library.png' });
    console.log('✓ Paper library loaded');
    
    // Check that Zotero Sync button is removed
    const zoteroButton = await page.locator('text=Zotero Sync').count();
    if (zoteroButton === 0) {
      console.log('✓ Zotero Sync button successfully removed');
    } else {
      console.error('✗ Zotero Sync button still exists!');
    }
    
    console.log('\nTest complete! Check the screenshots.');
    
  } catch (error) {
    console.error('Test failed:', error);
    await page.screenshot({ path: 'test-error.png' });
  } finally {
    await browser.close();
  }
}

testFrontend();