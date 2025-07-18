const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  console.log('1. Opening application at http://localhost:3000');
  await page.goto('http://localhost:3000');
  await page.waitForTimeout(2000);
  
  // Click "Get Started" button
  console.log('2. Clicking "Get Started" button');
  const getStartedButton = await page.$('button:has-text("Get Started")');
  if (getStartedButton) {
    await getStartedButton.click();
    await page.waitForTimeout(2000);
    
    await page.screenshot({ path: 'tmp/2-after-get-started.png', fullPage: true });
    console.log('Screenshot saved: 2-after-get-started.png');
    
    // Check if we're on the documents page
    const documentCards = await page.$$('.bg-white.rounded-lg.border');
    console.log(`Found ${documentCards.length} document cards`);
    
    if (documentCards.length > 0) {
      // Click on the first document
      console.log('3. Clicking on the first document');
      await documentCards[0].click();
      await page.waitForTimeout(3000);
      
      // Take screenshot of document view
      await page.screenshot({ path: 'tmp/3-document-view.png', fullPage: true });
      console.log('Screenshot saved: 3-document-view.png');
      
      // Look for the Overleaf button
      console.log('4. Looking for Overleaf button');
      const overleafButton = await page.$('button:has-text("Open in Overleaf")');
      
      if (overleafButton) {
        console.log('✓ Found Overleaf button');
        
        // Check button styling
        const buttonClass = await overleafButton.getAttribute('class');
        console.log(`Button classes: ${buttonClass}`);
        
        // Take close-up screenshot of header with button
        const header = await page.$('header');
        if (header) {
          await header.screenshot({ path: 'tmp/4-header-with-overleaf-button.png' });
          console.log('Screenshot saved: 4-header-with-overleaf-button.png');
        }
        
        // Get console messages
        page.on('console', msg => console.log('Browser console:', msg.text()));
        page.on('pageerror', error => console.log('Page error:', error.message));
        
        // Click the Overleaf button
        console.log('5. Clicking Overleaf button');
        
        // Listen for new page/tab
        const [newPage] = await Promise.all([
          context.waitForEvent('page').catch(() => null),
          overleafButton.click()
        ]);
        
        if (newPage) {
          console.log('✓ New tab opened');
          console.log(`New tab URL: ${newPage.url()}`);
          
          // Wait for Overleaf to load
          await newPage.waitForTimeout(5000);
          
          // Take screenshot of Overleaf
          await newPage.screenshot({ path: 'tmp/5-overleaf-page.png', fullPage: true });
          console.log('Screenshot saved: 5-overleaf-page.png');
          
          // Check if we're on Overleaf
          if (newPage.url().includes('overleaf.com')) {
            console.log('✓ Successfully navigated to Overleaf');
            
            // Check for login prompt or project view
            const loginForm = await newPage.$('form[action*="login"]');
            const projectView = await newPage.$('.project-list-react');
            const editorView = await newPage.$('.editor');
            
            if (loginForm) {
              console.log('→ Overleaf login page detected');
            } else if (projectView || editorView) {
              console.log('→ Overleaf project/editor view detected');
              
              // Look for files
              const fileTree = await newPage.$$('.entity-name');
              console.log(`Found ${fileTree.length} files in file tree`);
              
              for (let i = 0; i < fileTree.length; i++) {
                const fileName = await fileTree[i].textContent();
                console.log(`  File ${i + 1}: ${fileName}`);
              }
            }
          } else {
            console.log('✗ Not on Overleaf domain');
          }
        } else {
          console.log('✗ No new tab opened. Checking for errors...');
          
          // Check for any error messages
          const errorMessages = await page.$$('.text-red-500, .text-red-600, .error, .alert-danger');
          if (errorMessages.length > 0) {
            for (const error of errorMessages) {
              const text = await error.textContent();
              console.log(`Error message: ${text}`);
            }
          }
        }
        
      } else {
        console.log('✗ Overleaf button not found');
        
        // Check for Export button as reference
        const exportButton = await page.$('button:has-text("Export")');
        console.log(`Export button found: ${exportButton ? '✓' : '✗'}`);
        
        // Log all buttons in header
        const headerButtons = await page.$$('header button');
        console.log(`Total buttons in header: ${headerButtons.length}`);
        for (let i = 0; i < headerButtons.length; i++) {
          const text = await headerButtons[i].textContent();
          console.log(`  Button ${i + 1}: ${text}`);
        }
      }
      
    } else {
      console.log('No documents found. Please create a document first.');
      
      // Look for "New Document" button
      const newDocButton = await page.$('button:has-text("New Document")');
      if (newDocButton) {
        console.log('Found "New Document" button. You can create a test document.');
      }
    }
  } else {
    console.log('✗ "Get Started" button not found');
  }
  
  // Keep browser open for manual inspection
  console.log('\nTest completed. Browser will remain open for manual inspection.');
  console.log('Press Ctrl+C to close.');
  
})().catch(console.error);