const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  console.log('1. Opening application at http://localhost:3000');
  await page.goto('http://localhost:3000');
  await page.waitForTimeout(3000);
  
  // Take initial screenshot
  await page.screenshot({ path: 'tmp/1-homepage.png', fullPage: true });
  console.log('Screenshot saved: 1-homepage.png');
  
  // Check if there are any documents
  const documentCards = await page.$$('.bg-white.rounded-lg.border');
  console.log(`Found ${documentCards.length} document cards`);
  
  if (documentCards.length > 0) {
    // Click on the first document
    console.log('2. Clicking on the first document');
    await documentCards[0].click();
    await page.waitForTimeout(2000);
    
    // Take screenshot of document view
    await page.screenshot({ path: 'tmp/2-document-view.png', fullPage: true });
    console.log('Screenshot saved: 2-document-view.png');
    
    // Look for the Overleaf button
    console.log('3. Looking for Overleaf button');
    const overleafButton = await page.$('button:has-text("Open in Overleaf")');
    
    if (overleafButton) {
      console.log('✓ Found Overleaf button');
      
      // Check button styling
      const buttonClass = await overleafButton.getAttribute('class');
      console.log(`Button classes: ${buttonClass}`);
      
      // Get console messages
      page.on('console', msg => console.log('Browser console:', msg.text()));
      page.on('pageerror', error => console.log('Page error:', error.message));
      
      // Click the Overleaf button
      console.log('4. Clicking Overleaf button');
      
      // Listen for new page/tab
      const [newPage] = await Promise.all([
        context.waitForEvent('page'),
        overleafButton.click()
      ]);
      
      console.log('✓ New tab opened');
      console.log(`New tab URL: ${newPage.url()}`);
      
      // Wait for Overleaf to load
      await newPage.waitForTimeout(5000);
      
      // Take screenshot of Overleaf
      await newPage.screenshot({ path: 'tmp/3-overleaf-page.png', fullPage: true });
      console.log('Screenshot saved: 3-overleaf-page.png');
      
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
          const fileTree = await newPage.$('.file-tree');
          if (fileTree) {
            console.log('→ File tree found, checking for files...');
            const mainTex = await newPage.$('text=main.tex');
            const referencesBib = await newPage.$('text=references.bib');
            
            console.log(`main.tex found: ${mainTex ? '✓' : '✗'}`);
            console.log(`references.bib found: ${referencesBib ? '✓' : '✗'}`);
          }
        }
      } else {
        console.log('✗ Not on Overleaf domain');
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
    console.log('No documents found. Creating a test document...');
    
    // Click new document button
    const newDocButton = await page.$('button:has-text("New Document")');
    if (newDocButton) {
      await newDocButton.click();
      await page.waitForTimeout(2000);
      
      // Fill in document details
      const titleInput = await page.$('input[placeholder*="title"]');
      if (titleInput) {
        await titleInput.fill('Test Document for Overleaf Integration');
      }
      
      const createButton = await page.$('button:has-text("Create")');
      if (createButton) {
        await createButton.click();
        await page.waitForTimeout(2000);
        console.log('Test document created, please re-run the test');
      }
    }
  }
  
  // Keep browser open for manual inspection
  console.log('\nTest completed. Browser will remain open for manual inspection.');
  console.log('Press Ctrl+C to close.');
  
})().catch(console.error);