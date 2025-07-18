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
    
    // Click on Test3 Document (which has 0 citations, so we need to add some)
    console.log('3. Clicking on "Test3 Document"');
    const test3Doc = await page.$('text=Test3 Document');
    if (test3Doc) {
      await test3Doc.click();
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
        
        // Check if button is green
        const buttonColor = await overleafButton.evaluate(el => 
          window.getComputedStyle(el).backgroundColor
        );
        console.log(`Button background color: ${buttonColor}`);
        
        // Take close-up screenshot of header with button
        const header = await page.$('header, .flex.items-center.justify-between');
        if (header) {
          await header.screenshot({ path: 'tmp/4-header-with-overleaf-button.png' });
          console.log('Screenshot saved: 4-header-with-overleaf-button.png');
        }
        
        // Get console messages
        page.on('console', msg => {
          if (!msg.text().includes('Download the React DevTools')) {
            console.log('Browser console:', msg.text());
          }
        });
        page.on('pageerror', error => console.log('Page error:', error.message));
        
        // Click the Overleaf button
        console.log('5. Clicking Overleaf button');
        
        // Listen for new page/tab
        const newPagePromise = context.waitForEvent('page');
        await overleafButton.click();
        
        try {
          const newPage = await Promise.race([
            newPagePromise,
            new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 10000))
          ]);
          
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
            console.log(`Full Overleaf URL: ${newPage.url()}`);
            
            // Wait a bit more for potential redirects
            await newPage.waitForTimeout(3000);
            console.log(`Final URL after redirects: ${newPage.url()}`);
            
            // Check page content
            const pageTitle = await newPage.title();
            console.log(`Page title: ${pageTitle}`);
            
            // Look for various Overleaf elements
            const elements = {
              'Login form': 'form[action*="login"]',
              'Project list': '.project-list-react',
              'Editor': '.editor',
              'File tree': '.file-tree',
              'Entity names': '.entity-name',
              'Main content': '#main-content',
              'Create project button': 'button:has-text("Create")'
            };
            
            for (const [name, selector] of Object.entries(elements)) {
              const element = await newPage.$(selector);
              if (element) {
                console.log(`✓ Found: ${name}`);
              }
            }
            
            // Try to find any text mentioning the files
            const mainTexFound = await newPage.$('text=main.tex');
            const referencesFound = await newPage.$('text=references.bib');
            
            if (mainTexFound) console.log('✓ Found main.tex reference');
            if (referencesFound) console.log('✓ Found references.bib reference');
            
          } else {
            console.log('✗ Not on Overleaf domain');
            console.log(`Current URL: ${newPage.url()}`);
          }
        } catch (error) {
          console.log('✗ No new tab opened or timeout occurred');
          console.log(`Error: ${error.message}`);
          
          // Check for any error messages on the original page
          const errorMessages = await page.$$('.text-red-500, .text-red-600, .error, .alert-danger, .toast');
          if (errorMessages.length > 0) {
            console.log('Found error messages:');
            for (const error of errorMessages) {
              const text = await error.textContent();
              console.log(`  - ${text}`);
            }
          }
          
          // Check for loading states
          const loadingIndicators = await page.$$('.loading, .spinner, [aria-busy="true"]');
          if (loadingIndicators.length > 0) {
            console.log('Found loading indicators - button might still be processing');
          }
        }
        
      } else {
        console.log('✗ Overleaf button not found');
        
        // Check for Export button as reference
        const exportButton = await page.$('button:has-text("Export")');
        console.log(`Export button found: ${exportButton ? '✓' : '✗'}`);
        
        // Log all buttons
        const allButtons = await page.$$('button');
        console.log(`Total buttons on page: ${allButtons.length}`);
        for (let i = 0; i < Math.min(allButtons.length, 10); i++) {
          const text = await allButtons[i].textContent();
          const isVisible = await allButtons[i].isVisible();
          console.log(`  Button ${i + 1}: "${text.trim()}" (visible: ${isVisible})`);
        }
      }
    } else {
      console.log('✗ Could not find Test3 Document');
    }
  }
  
  // Keep browser open for manual inspection
  console.log('\nTest completed. Browser will remain open for manual inspection.');
  console.log('Press Ctrl+C to close.');
  
})().catch(console.error);