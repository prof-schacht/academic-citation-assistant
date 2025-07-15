# Development Scratchpad

## 2025-07-15: Updated Zotero Sync to Include PDF Attachments

### Problem
The Zotero sync was excluding attachments, which meant PDFs were not being downloaded. Without PDFs, we cannot build chunks for embedding search. The user correctly identified that we need to sync PDFs to enable the core citation recommendation feature.

### Solution
Updated the Zotero sync logic to:

1. **Fetch both papers AND their PDF attachments** in `_fetch_items_from_library`:
   - Changed return type to `Tuple[List[Dict], Dict[str, List[Dict]]]`
   - Returns papers and a dictionary mapping parent keys to their PDF attachments
   - Filters for PDF attachments specifically (contentType = "application/pdf")

2. **Updated `fetch_library_items`** to handle the new return format:
   - Aggregates papers and attachments from all selected libraries
   - Merges attachment dictionaries properly

3. **Improved PDF download logic** in `sync_library`:
   - Renamed `_download_attachment` to `_download_pdf_attachment` for clarity
   - Downloads PDFs using the attachment data fetched earlier
   - No need for separate API calls to get attachments

4. **Better logging**:
   - Reports number of papers AND PDF attachments fetched
   - Shows how many papers have PDF attachments available

### Files Modified
- `/backend/app/services/zotero_service.py` - Updated sync methods
- `/backend/test_zotero_sync.py` - Updated test to handle new return format
- `/backend/test_zotero_sync_with_pdfs.py` - New comprehensive test script

### How to Test
1. Run the updated test script:
   ```bash
   cd backend
   python test_zotero_sync_with_pdfs.py
   ```

2. The script will show:
   - Current papers and PDFs in the database
   - Number of papers and PDF attachments fetched
   - Sync results including newly downloaded PDFs
   - Example of newly added papers with PDF status

### Benefits
- Enables PDF processing for chunk creation and embeddings
- More efficient sync - fetches all data in one pass
- Better visibility into what's being synced
- Foundation for the citation recommendation engine

## 2025-07-15: Fixed Zotero Sync Duplicate DOI Issue

### Problem
The Zotero sync was failing with the error:
```
duplicate key value violates unique constraint 'ix_papers_doi'
```

This occurred because the Paper model has a unique constraint on the DOI field, and the sync was trying to insert papers with DOIs that already existed in the database.

### Solution
Updated the `sync_library` method in `zotero_service.py` to:

1. **Check for existing papers by DOI** before creating new ones:
   ```python
   # Check if paper with same DOI already exists
   existing_paper = None
   if metadata.get("doi"):
       result = await self.db.execute(
           select(Paper).where(Paper.doi == metadata["doi"])
       )
       existing_paper = result.scalar_one_or_none()
   ```

2. **Link Zotero items to existing papers** when DOI matches:
   - Uses the existing paper instead of creating a duplicate
   - Creates a ZoteroSync record to link the Zotero item to the existing paper
   - Updates empty metadata fields on the existing paper

3. **Proper transaction handling**:
   - Each item is committed individually
   - Rollback on errors to prevent partial updates
   - Continue processing other items even if one fails

4. **Fixed PDF download logic**:
   - Changed condition from `if not existing_sync and new_papers > 0` to `if not existing_sync and not paper.file_path`
   - This ensures PDFs are downloaded for newly linked papers that don't already have files

### Files Modified
- `/backend/app/services/zotero_service.py` - Updated `sync_library` method
- `/docs/usage.md` - Added documentation about duplicate DOI handling

### Test Script Created
- `/backend/test_zotero_duplicate_doi.py` - Test script to verify the fix

### How to Test
1. Run the test script:
   ```bash
   cd backend
   python test_zotero_duplicate_doi.py
   ```

2. The script will:
   - Show current papers with DOIs
   - Run a Zotero sync
   - Report new, updated, and failed papers
   - Check for any duplicate DOIs after sync

3. Expected result: No duplicate DOIs should be found after sync

### Benefits
- Prevents database constraint violations
- Allows multiple Zotero items to reference the same paper (by DOI)
- Maintains data integrity
- Provides better error handling and recovery