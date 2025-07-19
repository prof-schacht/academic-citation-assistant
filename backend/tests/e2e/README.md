# End-to-End Tests

This directory contains Playwright-based end-to-end tests for the Academic Citation Assistant.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install chromium
```

## Running Tests

### Enhanced Citations Test

To run the enhanced citations UI test:

```bash
# Make sure the application is running on http://localhost:3000
python test_enhanced_citations_ui.py
```

The test will:
- Open a browser window (set `headless=True` for CI/CD)
- Navigate to the document editor
- Enable enhanced citations
- Type academic text
- Verify citation suggestions appear
- Take a screenshot of the results

Screenshots will be saved as:
- `enhanced_citations_working.png` - Successful test
- `enhanced_citations_error.png` - If errors occur

## Test Results

The test verifies:
- Citation settings panel is visible
- Enhanced citations can be toggled
- Connection status shows "Connected"
- Citation suggestions appear when typing academic text
- WebSocket connection is established