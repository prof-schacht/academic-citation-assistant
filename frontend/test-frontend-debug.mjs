import { chromium } from '@playwright/test';

async function testFrontend() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Capture console messages
  page.on('console', msg => {
    console.log(`Console ${msg.type()}: ${msg.text()}`);
  });
  
  // Capture page errors
  page.on('pageerror', error => {
    console.error('Page error:', error.message);
  });
  
  try {
    console.log('1. Navigating to frontend...');
    await page.goto('http://localhost:3002', { waitUntil: 'networkidle' });
    
    // Take screenshot
    await page.screenshot({ path: 'test-homepage.png', fullPage: true });
    console.log('✓ Screenshot taken');
    
    // Get page content
    const title = await page.title();
    console.log('Page title:', title);
    
    // Check what's visible on the page
    const visibleText = await page.evaluate(() => document.body.innerText);
    console.log('Page content preview:', visibleText.substring(0, 200));
    
    // Check for specific elements
    const hasDocumentsLink = await page.locator('text=Documents').count();
    console.log('Documents link found:', hasDocumentsLink > 0);
    
    const hasPaperLibraryLink = await page.locator('text=Paper Library').count();
    console.log('Paper Library link found:', hasPaperLibraryLink > 0);
    
    // Try clicking on visible links
    if (hasDocumentsLink > 0) {
      console.log('Clicking on Documents...');
      await page.click('text=Documents');
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'test-documents.png' });
    }
    
  } catch (error) {
    console.error('Test failed:', error);
    await page.screenshot({ path: 'test-error.png' });
  } finally {
    console.log('Keeping browser open for manual inspection...');
    await page.waitForTimeout(30000); // Keep open for 30 seconds
    await browser.close();
  }
}

testFrontend();