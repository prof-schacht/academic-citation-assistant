# Development Scratchpad

## 2025-07-15: Fixing Zotero Collection Sync Issue

### Problem
The Zotero sync is failing when collections are selected in the old format (just collection keys without library IDs). The system needs to handle both formats:
1. Old format: `["CPUVP4AQ", "OTHERKEY"]` - just collection keys
2. New format: `[{"key": "CPUVP4AQ", "libraryId": "groups/123456"}]` - with library context

### Analysis
Looking at the current implementation in `zotero_service.py`:

1. **Lines 110-127**: The code attempts to parse selected collections and handle both formats
2. **Lines 142-155**: When old-format collections are detected without library info, it tries to fetch from all libraries
3. **Lines 170-176**: Collection filtering is applied per library

The issue is that when collections are in old format, the system doesn't efficiently find which library contains those collections.

### Solution Plan
1. Implement a more robust collection filtering logic that:
   - Searches all available libraries when collections are in old format
   - Prioritizes the user's personal library first
   - Caches collection-to-library mappings for efficiency

2. Add a migration function to convert old format collections to new format

3. Improve logging to better debug collection matching issues

4. Add comprehensive tests to ensure both formats work correctly

### Implementation Steps
1. ✓ Update `fetch_library_items` method to better handle old format collections
   - Added detection of old format collections
   - When old format is detected, search all available libraries
   - Create a mapping of collection keys to library IDs
   - Apply correct filtering per library
   
2. ✓ Add better logging for collection discovery
   - Log which collections are found in which libraries
   - Log collections that aren't found anywhere
   - Better debug logging for item filtering

3. ✓ Implement collection format migration (`migrate_collection_format`)
   - Discovers which library contains each old-format collection
   - Converts to new format with library IDs
   - Updates the database configuration
   
4. Next: Create a test to verify the fix works
5. Next: Run tests and validate the implementation