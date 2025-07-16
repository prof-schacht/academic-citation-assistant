import { chromium } from '@playwright/test';

async function takeScreenshots() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    // Homepage
    await page.goto('http://localhost:3002');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'screenshot-homepage.png', fullPage: true });
    
    // Documents page
    await page.click('text=Get Started');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'screenshot-documents.png', fullPage: true });
    
    // Editor page
    await page.goto('http://localhost:3002/editor');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'screenshot-editor.png', fullPage: true });
    
    console.log('Screenshots taken successfully!');
    
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await browser.close();
  }
}

takeScreenshots();