# Academic Citation Assistant - Content Restoration Fix

## Issue Analysis
The saved content is not being restored when switching back to the editor tab because:

1. The Editor component is unmounted when switching to other tabs (bibliography/citations)
2. When the Editor remounts, it uses the initial document.content value which is stale
3. The LoadInitialContentPlugin only runs once with the initial content

## Solution
We need to reload the document content when switching back to the editor tab to ensure we have the latest saved content.

## Implementation Steps
1. Add a mechanism to reload document content when switching to editor tab
2. Update the Editor component to handle content updates properly
3. Ensure the LoadInitialContentPlugin can handle content updates

## Testing
After implementation, test by:
1. Creating/loading a document
2. Adding content in the editor
3. Switching to bibliography tab (content should auto-save)
4. Switching back to editor tab (content should be restored)