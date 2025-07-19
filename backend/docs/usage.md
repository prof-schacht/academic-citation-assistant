# Academic Citation Assistant - Usage Guide

## Running the Application

### Backend Server
```bash
cd backend
npm install
npm run dev
```

The backend server will start on http://localhost:5000

### Frontend Application
```bash
cd frontend
npm install
npm run dev
```

The frontend application will be available at http://localhost:3000

## Testing Enhanced Citations

### End-to-End UI Test

We have a Playwright test that verifies the enhanced citations feature works correctly in the browser.

#### Setup
1. Install test dependencies:
```bash
cd backend/tests/e2e
pip install -r requirements.txt
playwright install chromium
```

#### Running the Test
1. Make sure both backend and frontend are running
2. Run the test:
```bash
python test_enhanced_citations_ui.py
```

The test will:
- Open a browser window and navigate to the document editor
- Enable the "Enhanced Citations" toggle
- Type academic text in the editor
- Wait for and verify citation suggestions appear
- Check that the WebSocket connection status shows "Connected"
- Take a screenshot of the working feature

#### Test Output
- **Success**: Screenshot saved as `enhanced_citations_working.png`
- **Failure**: Error screenshot saved as `enhanced_citations_error.png`

### Manual Testing

To manually test enhanced citations:

1. Open http://localhost:3000/editor in your browser
2. Look for the citation settings panel on the right side
3. Toggle "Enhanced Citations" to enable the feature
4. Start typing academic text, for example:
   - "Recent advances in machine learning..."
   - "The transformer architecture by Vaswani et al..."
   - "Studies on climate change have shown..."
5. Citation suggestions should appear as you type
6. The connection status should show "Connected"

## Features

### Document Editor
- Real-time citation suggestions as you type
- Citation formatting in multiple styles (APA, MLA, Chicago)
- Export options for your document with citations

### Citation Management
- Search and browse citation database
- Save citations to your library
- Import citations from external sources

### Enhanced Citations (Real-time)
- WebSocket-based real-time suggestions
- Semantic search using vector embeddings
- Context-aware recommendations based on your text

## Troubleshooting

### Citations Not Appearing
1. Check that enhanced citations is enabled in settings
2. Verify connection status shows "Connected"
3. Check browser console for errors (F12)
4. Ensure backend server is running on port 5000

### Connection Issues
1. Verify backend is running: `curl http://localhost:5000/health`
2. Check WebSocket connection in browser dev tools
3. Look for CORS errors in console
4. Try refreshing the page

### Test Failures
If the Playwright test fails:
1. Check the error screenshot for visual clues
2. Ensure both servers are running
3. Check browser console output in test logs
4. Verify no port conflicts (3000, 5000)