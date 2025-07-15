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