# Academic Citation Assistant - Development Scratchpad

## July 17, 2025 - Citation Auto-Save Fix

### Issue
After inserting a citation through the citation panel, the document would not auto-save. Users had to type additional text for the save to trigger.

### Root Cause
The citation insertion happens programmatically through `editor.update()` in CitationInsertPlugin, which doesn't always trigger the onChange event that initiates auto-save in the Editor component.

### Solution
Added a manual save trigger in `handleCitationInserted` in DocumentEditor.tsx:
- After citation insertion and bibliography update, explicitly call the editor's save function
- Added 100ms delay to ensure editor state is fully updated
- This ensures documents save after citation insertion without requiring additional user input

### Files Modified
- `frontend/src/pages/DocumentEditor.tsx` - Added manual save trigger
- `frontend/src/components/Editor/Editor.tsx` - Added debug logging
- `frontend/package.json` - Updated version to 0.0.1
- `frontend/src/pages/HomePage.tsx` - Added version display
- `docs/usage.md` - Documented the fix

### Test Plan
Created Playwright test in `tests/test_citation_insertion_save.spec.ts` to verify:
1. Document saves after citation insertion
2. onChange events fire correctly
3. Editor maintains focus after insertion

---

# Zotero Sync Fix - Development Process

## Issues Identified (2025-07-15)

1. **Frontend not showing saved groups**: 
   - Database shows COAI is saved as `["groups/4965330"]` 
   - Frontend doesn't show it as selected when loading
   - The `/status` endpoint doesn't return selected_groups/selected_collections

2. **Sync not fetching from selected groups**: 
   - The COAI group has 2268 items but the sync returned "0 new"
   - Issue in `_fetch_items_from_library` method - wrong URL format

3. **Only 5 papers in library**: 
   - These seem to be from previous tests, not from COAI

## Root Causes

1. **Status endpoint missing data**: The `/zotero/status` endpoint doesn't return `selected_groups` and `selected_collections`
2. **Wrong API URL format**: In `_fetch_items_from_library`, the URL is built as `/users/12345/items` or `/groups/67890/items` but the library_id already contains the prefix
3. **Frontend doesn't load saved selections**: Even if the backend returned the data, the frontend doesn't use it

## Fixes Implemented

### Backend Changes (app/api/zotero.py)
1. ✅ Updated `ZoteroConfigResponse` model to include `selected_groups` and `selected_collections`
2. ✅ Modified `/configure` endpoint to return selected groups/collections
3. ✅ Modified `/status` endpoint to return selected groups/collections
4. ✅ Added json import

### Backend Changes (app/services/zotero_service.py)
1. ✅ Added comment to clarify that library_id already contains the prefix

### Frontend Changes (src/services/zoteroService.ts)
1. ✅ Updated `ZoteroStatus` interface to include `selectedGroups` and `selectedCollections`
2. ✅ Updated `mapStatus` method to map the new fields

### Frontend Changes (src/pages/ZoteroSettings.tsx)
1. ✅ Updated `loadStatus` to set selected groups/collections from the status response

## Next Steps
1. Test the sync functionality with the COAI group
2. Verify that the frontend properly shows selected groups when reloading the page
3. Check that sync fetches papers from the selected group

---

# Database Initialization Fix - Development Process

## Issue Summary (2025-07-17)
Fresh installation on new PC resulted in "relation 'documents' does not exist" error when accessing documents page.

## Root Cause
Database migrations were not run after starting Docker containers, leaving the database without any tables.

## Investigation Process
1. Explored codebase structure to understand database setup
2. Found that project uses Alembic for database migrations
3. Discovered existing migration files ready to create all tables
4. Located docker-rebuild.sh script showing proper setup process

## Solution Implementation
1. Ran database migrations:
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

2. Populated test data:
   ```bash
   docker-compose exec backend python scripts/populate_test_papers_v2.py
   ```

3. Verified API endpoints were working:
   - `/api/papers/` - returned 4 papers
   - `/api/documents/` - returned empty list (expected)

## Documentation Updates
1. Updated `docs/usage.md`:
   - Added migration step to Quick Start section
   - Added database initialization to troubleshooting section
   - Added note about fresh installation requirements

2. Created `tmp/fresh-installation-guide.md`:
   - Comprehensive guide for new installations
   - Included complete reset instructions
   - Added verification steps

3. Updated version number:
   - Version: 1.3.1
   - Build: 20250117-002-DB-INIT-FIX

## Key Learnings
- Database migrations must be explicitly run on fresh installations
- The docker-compose up command starts containers but doesn't run migrations
- Clear documentation of initialization steps prevents user frustration

## Testing Notes
To test the fix on a fresh installation:
1. Stop and remove all containers and volumes: `docker-compose down -v`
2. Start containers: `docker-compose up -d`
3. Run migrations: `docker-compose exec backend alembic upgrade head`
4. Access the application and verify no database errors occur

---

# Admin Clean Papers Fix - Development Process

## Issue Summary (2025-07-17)
User wanted to delete all papers from the database but got an error: "AttributeError: DATA_MANAGEMENT"

## Root Cause
The LogCategory enum didn't have a DATA_MANAGEMENT value. The valid categories are:
- ZOTERO_SYNC
- PDF_PROCESSING  
- SYSTEM
- AUTH
- API
- DATABASE
- SEARCH

## Solution Implementation
1. Fixed the LogCategory error by changing DATA_MANAGEMENT to DATABASE in admin.py
2. Added a new clean_all_papers function to delete papers:
   - Deletes paper chunks first (foreign key constraint)
   - Then deletes all papers
   - Returns count of deleted items
3. Added new API endpoint: POST /api/admin/clean-papers

## API Usage
```bash
# Delete all papers
curl -X POST http://localhost:8000/api/admin/clean-papers \
  -H "Content-Type: application/json" \
  -d '{"confirmation": "DELETE ALL"}'

# Delete all documents  
curl -X POST http://localhost:8000/api/admin/clean-documents \
  -H "Content-Type: application/json" \
  -d '{"confirmation": "DELETE ALL"}'
```

## Test Results
- Successfully deleted 9 papers from the database
- Papers endpoint now returns empty array
- Both clean operations working correctly

---

# Paper Processing Error Fix - Development Process

## Issue Summary (2025-07-17)
Paper upload resulted in "'Paper' object has no attribute 'user_id'" error and processing failures were not appearing in system logs.

## Root Cause
The Paper model doesn't have a user_id attribute (papers are shared resources, not owned by users), but the paper_processor.py was trying to access paper.user_id in three places for logging.

## Solution Implementation
1. Removed user_id references from log_async_info calls (lines 61, 142)
2. Removed user_id reference from log_async_error call (line 165)
3. Ensured error logging happens even when paper lookup fails

## Changes Made
- `/backend/app/services/paper_processor.py`:
  - Removed `user_id=paper.user_id` from all logging calls
  - Log functions now work without user context for paper processing
  - Error logging now happens for all failures, not just when paper exists

## Test Results
- Paper upload now works successfully
- Processing logs appear in system logs view
- Both start and completion of processing are logged
- Errors are properly logged with stack traces

## Version Update
- Version: 1.3.3
- Build: 20250117-004-FIX-PAPER-PROCESSING

---

# Test User Creation Fix - Development Process

## Issue Summary (2025-07-17)
Document creation failed with foreign key constraint error: "Key (owner_id)=(00000000-0000-0000-0000-000000000001) is not present in table 'users'."

## Root Cause
The test user with UUID 00000000-0000-0000-0000-000000000001 didn't exist in the users table. Documents require a valid owner_id that references an existing user.

## Solution Implementation
1. Created simplified test user creation script (without passlib dependency)
2. Added test user creation to fresh installation steps
3. Updated documentation to include user creation step

## Files Created/Modified
- Created: `/backend/scripts/create_test_user_simple.py`
- Updated: `/tmp/fresh-installation-guide.md`
- Updated: `/docs/usage.md`

## Test Results
- Test user created successfully
- Document creation now works
- API and frontend can create documents without errors

## Version Update
- Version: 1.3.4
- Build: 20250117-005-ADD-TEST-USER

---

# NLTK Data Download Fix - Development Process

## Issue Summary (2025-07-17)
Citation recommendations were failing with error: "Resource punkt_tab not found"

## Root Cause
NLTK's sentence tokenizer requires the punkt_tab data package to be downloaded, but it wasn't being installed on fresh installations.

## Solution Implementation
1. Updated text_analysis.py to try punkt_tab first, then fallback to punkt
2. Added NLTK data download to application startup in main.py
3. Created download_nltk_data.py script for manual setup
4. Updated docker-rebuild.sh to include NLTK data download

## Files Created/Modified
- Modified: `/backend/app/services/text_analysis.py`
- Modified: `/backend/app/main.py`
- Created: `/backend/scripts/download_nltk_data.py`
- Updated: `/backend/docker-rebuild.sh`
- Updated: `/tmp/fresh-installation-guide.md`

## Test Results
- NLTK data downloads automatically on startup
- Citation recommendations now work properly
- Fallback mechanisms in place for compatibility

## Version Update
- Version: 1.3.5
- Build: 20250117-006-NLTK-DATA-FIX

---

# LaTeX-Style Citations Implementation - Development Process

## Issue Summary (2025-07-17)
User requested LaTeX-style citations with citation keys (e.g., \cite{citationkey}) displayed as icons with hover tooltips, and citations should be placed at the end of sentences.

## Requirements Implemented
1. LaTeX-style citation keys (e.g., Smith2023Machine)
2. Visual citation icon instead of full text
3. Hover tooltip showing paper details
4. Citations placed at end of sentence when inserted mid-sentence
5. Hidden LaTeX \cite{} command for copy/export

## Solution Implementation

### 1. Created Custom Citation Node
- `CitationNode.tsx`: Custom Lexical node for citations
- Stores citation key, paper metadata
- Renders as small icon with citation key
- Includes hover tooltip with paper details
- Hidden LaTeX command for accessibility

### 2. Citation Key Generation
- `citationUtils.ts`: Generates citation keys
- Format: AuthorYearFirstWord (e.g., Smith2023Machine)
- Fallback to paper ID if metadata incomplete

### 3. Updated Citation Insertion
- Modified `CitationInsertPlugin.tsx`
- Finds end of current sentence
- Places citation at sentence end
- Uses custom node instead of plain text

### 4. Visual Design
- Small blue citation icon with paper icon
- Citation key displayed in monospace font
- Hover tooltip shows:
  - Full paper title
  - Authors (formatted as "Author et al.")
  - Year of publication
- Hidden \cite{} command for screen readers

## Files Created/Modified
- Created: `/frontend/src/components/Editor/nodes/CitationNode.tsx`
- Created: `/frontend/src/utils/citationUtils.ts`
- Modified: `/frontend/src/components/Editor/plugins/CitationInsertPlugin.tsx`
- Modified: `/frontend/src/components/Editor/EditorConfig.ts`

## Version Update
- Version: 1.4.0
- Build: 20250117-007-LATEX-CITATIONS

---

# Data Persistence Fixes - Development Process

## Issue Summary (2025-07-17)
1. Text was lost when switching between tabs (Editor → Bibliography → Editor)
2. Citations were not persisting after saving and reopening documents

## Root Causes
1. **Tab switching**: Editor component was canceling pending saves on unmount instead of flushing them
2. **Citation persistence**: Citation nodes were properly serialized but needed React import for JSX support

## Solution Implementation

### 1. Fixed Tab Switching Data Loss
- Changed `debouncedSave.cancel()` to `debouncedSave.flush()` on component unmount
- Added `handleTabChange` function that saves before switching tabs
- Exposed save function from Editor via `onEditorReady` callback

### 2. Fixed Citation Persistence
- Citation nodes already had proper `exportJSON` and `importJSON` methods
- Added React import for JSX.Element type support
- Citations now properly serialize/deserialize with documents

### 3. Enhanced Auto-Save
- Save is triggered when:
  - Content changes (2-second debounce)
  - Tab is switched
  - Component unmounts
  - Manual save (Ctrl/Cmd+S)

## Files Modified
- `/frontend/src/components/Editor/Editor.tsx`
  - Changed unmount behavior from cancel to flush
  - Added onEditorReady prop
- `/frontend/src/pages/DocumentEditor.tsx`
  - Added handleTabChange to save before switching
  - Connected editorSaveRef for manual saves
- `/frontend/src/components/Editor/nodes/CitationNode.tsx`
  - Added React import for type support

## Test Results
- Text no longer lost when switching tabs
- Citations persist after save and reload
- Auto-save works reliably in all scenarios

## Version Update
- Version: 1.4.1
- Build: 20250117-008-FIX-DATA-PERSISTENCE

---

# Document Save Issue Analysis - Citation Insertion

## Problem Statement (2025-07-17)
Content might not be saved when quickly clicking away from the editor after inserting a citation.

## Key Findings

### 1. Debounced Save Mechanism
- Editor uses a debounced save with default delay of 2000ms (2 seconds)
- Located in `Editor.tsx` lines 112-132
- The save is triggered on content changes via `OnChangePlugin`

### 2. Save Triggers
- **Auto-save**: Triggered after 2 seconds of no changes
- **Manual save**: 
  - On tab change (DocumentEditor.tsx line 165)
  - On component unmount (Editor.tsx line 157)
  - On keyboard shortcut (Cmd/Ctrl+S)

### 3. Citation Insertion Flow
1. User clicks "Insert" button in CitationPanel
2. Citation is inserted via CitationInsertPlugin
3. Editor content changes, triggering debounced save
4. If user immediately clicks away (e.g., to Bibliography tab), the save might not complete

### 4. Root Cause Analysis
- The 2-second debounce delay means content changes need 2 seconds to auto-save
- Tab switching does call `debouncedSave.flush()` but only if `editorSaveRef.current` is properly set
- There's a potential race condition between citation insertion and tab switching
- The save on unmount was already fixed (using flush instead of cancel)

### 5. Current Save Implementation
```javascript
// In Editor.tsx
const debouncedSave = useCallback(
  debounce(async (editorState: EditorState) => {
    // ... save logic
  }, autoSaveDelay), // 2000ms default
  [documentId, onSave, autoSaveDelay]
);

// Save triggers:
// 1. On change (debounced)
// 2. On unmount (flush)
// 3. On tab change (flush via editorSaveRef)
```

### Potential Solutions
1. **Force immediate save after citation insertion** - Most reliable
2. Reduce debounce delay for citation insertions
3. Add save confirmation before tab switching
4. Show more prominent save status indicator
5. Disable UI interactions briefly after citation insertion