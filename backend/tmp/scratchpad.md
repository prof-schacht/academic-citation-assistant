# Development Scratchpad

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