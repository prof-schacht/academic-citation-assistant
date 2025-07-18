import { chromium } from '@playwright/test';

async function testFrontend() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Capture console errors
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });
  
  try {
    console.log('=== Testing Academic Citation Assistant Frontend ===\n');
    
    // 1. Test Homepage
    console.log('1. Testing Homepage...');
    await page.goto('http://localhost:3002');
    await page.waitForLoadState('networkidle');
    
    const title = await page.title();
    console.log(`   ✓ Page loaded (title: ${title})`);
    
    // Check for main elements
    const hasGetStarted = await page.locator('text=Get Started').count() > 0;
    console.log(`   ✓ Get Started button found: ${hasGetStarted}`);
    
    // 2. Navigate to Documents
    console.log('\n2. Testing Documents Page...');
    await page.click('text=Get Started');
    await page.waitForURL('**/documents');
    console.log('   ✓ Navigated to documents page');
    
    // Check documents page elements
    const hasLibraryLink = await page.locator('text=Paper Library').count() > 0;
    console.log(`   ✓ Paper Library link found: ${hasLibraryLink}`);
    
    // 3. Navigate to Paper Library
    console.log('\n3. Testing Paper Library...');
    if (hasLibraryLink) {
      await page.click('text=Paper Library');
      await page.waitForURL('**/library');
      console.log('   ✓ Navigated to paper library');
      
      // Check that Zotero Sync button is removed
      const zoteroButton = await page.locator('text=Zotero Sync').count();
      console.log(`   ✓ Zotero Sync button removed: ${zoteroButton === 0}`);
      
      // Check for assign button on papers
      const hasUploadButton = await page.locator('text=Upload Papers').count() > 0;
      console.log(`   ✓ Upload Papers button found: ${hasUploadButton}`);
    }
    
    // 4. Test Document Editor
    console.log('\n4. Testing Document Editor...');
    await page.goto('http://localhost:3002/editor');
    await page.waitForLoadState('networkidle');
    
    // Check for tabs
    const hasEditorTab = await page.locator('text=Editor').count() > 0;
    const hasBibliographyTab = await page.locator('text=Bibliography').count() > 0;
    const hasCitationsTab = await page.locator('text=Citations').count() > 0;
    
    console.log(`   ✓ Editor tab found: ${hasEditorTab}`);
    console.log(`   ✓ Bibliography tab found: ${hasBibliographyTab}`);
    console.log(`   ✓ Citations tab found: ${hasCitationsTab}`);
    
    // Click Bibliography tab
    if (hasBibliographyTab) {
      await page.click('text=Bibliography');
      await page.waitForTimeout(500);
      
      const hasAddPapers = await page.locator('text=Add Papers').count() > 0;
      console.log(`   ✓ Add Papers button in bibliography: ${hasAddPapers}`);
    }
    
    // 5. Test Export Dialog
    console.log('\n5. Testing Export Dialog...');
    const hasExportButton = await page.locator('text=Export').count() > 0;
    if (hasExportButton) {
      await page.click('text=Export');
      await page.waitForTimeout(500);
      
      const hasBibTeX = await page.locator('text=BibTeX').count() > 0;
      const hasLaTeX = await page.locator('text=LaTeX').count() > 0;
      
      console.log(`   ✓ BibTeX export option: ${hasBibTeX}`);
      console.log(`   ✓ LaTeX export option: ${hasLaTeX}`);
      
      // Close dialog
      await page.keyboard.press('Escape');
    }
    
    // Summary
    console.log('\n=== Test Summary ===');
    console.log(`Console errors: ${consoleErrors.length}`);
    if (consoleErrors.length > 0) {
      console.log('Errors found:');
      consoleErrors.forEach(err => console.log(`  - ${err}`));
    }
    
    console.log('\n✅ All tests completed!');
    
  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    await page.screenshot({ path: 'test-error.png' });
    throw error;
  } finally {
    await browser.close();
  }
}

testFrontend().catch(console.error);