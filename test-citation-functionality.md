# Testing Citation Functionality

## What's been implemented:

### 1. **Insert Citation Functionality** ✅
- Created `CitationInsertPlugin.tsx` that handles inserting citations into the Lexical editor
- The plugin formats citations properly: `(Author et al., Year)` for papers with metadata
- Falls back to `[paper-id]` for papers without proper metadata
- Connected the CitationPanel to the Editor through props

### 2. **Improved Metadata Extraction** ✅
- Enhanced title extraction to look for title-case patterns in first 50 lines
- Improved author extraction with better pattern matching and cleanup
- Successfully extracted metadata from one test paper:
  - Title: "TOWARDS MACHINE THEORY OF MIND WITH"
  - Authors: ["Rebekah A. Gelp´ı", "Eric Xue", "and William A. Cunningham"]
  - Year: 2024

### 3. **Current State of Papers**:
- 3 uploaded papers (2 still show filenames as titles)
- 4 test papers with proper metadata
- Citation suggestions now show better information for papers with metadata

## How to test:

1. **Test Insert Citation**:
   - Open a document in the editor
   - Start typing about machine learning or AI
   - Wait for citation suggestions to appear
   - Click "Insert" on any suggestion
   - The citation should be inserted at your cursor position

2. **Test Citation Format**:
   - Papers with metadata: `(Gelp´ı et al., 2024)`
   - Papers without metadata: `[8f12311d-49e2-490f-87e0-27634fc7b832]`

## What still needs work:

1. **View Details** - Not implemented yet
2. **Add to Library** - Not implemented yet
3. **Better PDF metadata extraction** - Only 1 of 3 PDFs extracted properly
4. **Citation formatting options** - Currently only supports one format

## Files Modified:

1. `frontend/src/components/Editor/plugins/CitationInsertPlugin.tsx` - NEW
2. `frontend/src/components/Editor/Editor.tsx` - Added citation insert support
3. `frontend/src/pages/DocumentEditor.tsx` - Connected citation insert handler
4. `frontend/src/components/CitationPanel/CitationPanel.tsx` - Connected insert button
5. `backend/app/services/paper_processor.py` - Improved metadata extraction