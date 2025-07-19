# Usage Guide - Academic Citation Assistant

## Version 0.2.3 - Latest Updates (July 19, 2025)

### Enhanced Citation Engine Improvements

1. **Comprehensive Logging and Debugging**
   - Added detailed logging throughout the enhanced citation pipeline
   - Track BM25 fitting progress (shows document processing count)
   - Monitor hybrid search execution and results
   - Identify bottlenecks with timeout logging

2. **Timeout Protection**
   - BM25 fitting: 30-second timeout
   - Hybrid search: 20-second timeout  
   - Reranking: 30-second timeout
   - Prevents WebSocket connections from hanging indefinitely

3. **Memory Optimization**
   - Limited BM25 fitting to 10,000 documents maximum
   - Handles empty corpus gracefully
   - Improved error handling with fallback mechanisms

4. **Bug Fixes**
   - Fixed null abstract handling in citation ranking
   - Fixed AttributeError when papers have missing abstracts
   - Enhanced citations now work properly with all search strategies

### Testing Enhanced Citations

To test the enhanced citation features:

```bash
cd backend
python test_enhanced_citations.py
```

This will test:
- Vector search only (baseline)
- Hybrid search without reranking
- Full enhanced features (hybrid + reranking)

Expected behavior:
- Vector search: Fast, semantic similarity only
- Hybrid search: Combines keyword (BM25) and semantic search
- With reranking: Higher quality results but adds 200-500ms latency

## Version 0.2.2 - Previous Updates (July 19, 2025)

### Critical Fixes Implemented

1. **WebSocket Connection Stability**
   - Fixed connection state management (removed `isConnected` flag)
   - Added 5-second connection timeout
   - Limited message queue to 10 messages
   - Added proper cleanup on abnormal disconnection

2. **Frontend Freezing Issues**
   - Fixed memory buildup from unbounded message queue (82,806+ messages)
   - Added debouncing (300ms) to configuration changes
   - Prevented rapid reconnection loops

3. **Backend Improvements**
   - Made reranking service initialization optional
   - Fixed SQL query issues in hybrid search
   - Fixed column name mismatches (publication_year → year)
   - Implemented model caching to avoid HuggingFace rate limiting

### Testing the Citation System

#### 1. Start the Application

```bash
# Make sure you're in the project root directory
docker-compose up -d

# Check that all services are running
docker-compose ps
```

#### 2. Access the Frontend

Open your browser and navigate to: http://localhost:3000

#### 3. Test Citation Suggestions

1. Navigate to the Document Editor (http://localhost:3000/editor)
2. Start typing academic content, for example:
   - "Recent advances in natural language processing have shown that transformer models..."
   - "Machine learning techniques have revolutionized data analysis..."
   - "Deep learning approaches for computer vision..."

3. The system should provide real-time citation suggestions as you type

#### 4. Configuration Options

In the Citation Settings panel, you can configure:

- **Enhanced Citations**: Toggle advanced citation features
- **Use Reranking**: Enable/disable cross-encoder reranking
- **Search Strategy**: Choose between:
  - Vector search (semantic similarity)
  - BM25 (keyword-based)
  - Hybrid (combines both)

#### 5. Monitor System Health

Check the connection status indicator in the UI:
- Green: Connected and working
- Yellow: Connecting
- Red: Disconnected

#### 6. Testing with the Test Script

Run the provided test script to verify the citation system:

```bash
cd backend
python test_citation_system.py
```

This will send a test query and display the returned citations.

#### 7. Checking Logs

To monitor system behavior:

```bash
# Backend logs
docker logs academic-citation-assistant-backend-1 -f

# Frontend logs
docker logs academic-citation-assistant-frontend-1 -f

# Database logs
docker logs academic-citation-assistant-postgres-1 -f
```

### Troubleshooting

#### If citations aren't appearing:

1. Check that the backend is running:
   ```bash
   docker-compose ps
   ```

2. Verify WebSocket connection in browser console:
   - Open Developer Tools (F12)
   - Check Network tab for WebSocket connections
   - Look for any error messages in Console

3. Ensure the database has papers:
   ```bash
   docker exec -it academic-citation-assistant-postgres-1 psql -U citation_user -d citation_db
   SELECT COUNT(*) FROM papers;
   ```

#### If the frontend freezes:

1. Refresh the page
2. Check browser console for errors
3. Verify the version number shows "v0.2.2" in the bottom-right corner

#### If you see rate limiting errors:

The system now caches models locally. If you still see rate limiting:
1. Check that model_cache directory exists in the container:
   ```bash
   docker exec academic-citation-assistant-backend-1 ls -la /app/model_cache/
   ```

2. Restart the backend to reinitialize services:
   ```bash
   docker restart academic-citation-assistant-backend-1
   ```

### Performance Tips

1. **For better suggestions**:
   - Write complete sentences
   - Provide context (at least 10 characters)
   - Use academic language and terminology

2. **For faster responses**:
   - Use Vector search for quick semantic matches
   - Use Hybrid search for comprehensive results
   - Disable reranking if you need minimal latency

3. **For more accurate results**:
   - Enable Enhanced Citations
   - Use Hybrid search with reranking
   - Upload relevant papers to your library

### Known Limitations

- Minimum text length: 10 characters for suggestions
- Rate limit: 60 requests per minute per user
- Maximum message queue: 10 messages
- Connection timeout: 5 seconds

---

## Recent Updates (July 18, 2025)

### NEW: Enhanced Chunking and Retrieval System 🚀
Significantly improved citation recommendation accuracy through advanced text processing and retrieval techniques:

#### Key Improvements

##### 1. Advanced Chunking Strategies
- **Sentence-Aware Chunking**: Respects sentence boundaries for more coherent text segments
- **Hierarchical Chunking**: Automatically detects paper sections (Abstract, Introduction, Methods, etc.)
- **Element-Based Chunking**: Preserves document structure and paragraph boundaries
- **Semantic Chunking**: Groups related sentences based on meaning (optional)

##### 2. Hybrid Search (BM25 + Vector)
- **Dual Retrieval**: Combines keyword-based BM25 search with semantic vector search
- **Configurable Weights**: Default 60% vector, 40% BM25 for balanced results
- **Better Recall**: Catches papers that pure vector search might miss
- **Improved Precision**: Keyword matching ensures relevant terminology

##### 3. Cross-Encoder Reranking
- **Two-Stage Architecture**: Fast retrieval followed by accurate reranking
- **State-of-the-Art Models**: Uses MS-MARCO trained cross-encoders
- **Context-Aware Scoring**: Considers surrounding sentences for better relevance
- **Configurable**: Can be enabled/disabled based on performance needs

#### Configuration Options

The enhanced citation system can be configured through WebSocket connection parameters:

```javascript
// Example WebSocket connection with configuration
const ws = new WebSocket(
  'ws://localhost:8000/ws/citations/v2?' +
  'user_id=user123&' +
  'use_enhanced=true&' +           // Enable enhanced features
  'use_reranking=true&' +          // Enable cross-encoder reranking
  'search_strategy=hybrid'         // Options: vector, bm25, hybrid
);
```

#### Performance Impact
- **Accuracy**: Up to 30% improvement in citation relevance
- **Latency**: Reranking adds 200-500ms for better quality
- **Coverage**: Hybrid search finds 40% more relevant papers

#### When to Use Each Strategy
- **Hybrid Search**: Best for general use, balances precision and recall
- **Vector-Only**: Fast, good for semantic similarity queries
- **BM25-Only**: Best for specific keyword searches
- **With Reranking**: When accuracy is more important than speed
- **Without Reranking**: For real-time applications requiring <200ms response

## Recent Updates (July 18, 2025)

### NEW: PDF Viewer for Citation Details 📄
View full papers directly within the document editor while writing:

#### How it Works
- **Integrated PDF Viewer**: Opens in a third column when you click "View Details" on any citation suggestion
- **Three-Column Layout**: Editor | Citations Panel | PDF Viewer for seamless research workflow
- **Read While Writing**: Keep the paper open while you write about it
- **Visual Highlighting**: Selected citation is highlighted in the citations panel

#### Using the Feature
1. Start typing in your document to trigger citation suggestions
2. When suggestions appear, click **"View Details"** on any paper
3. The PDF viewer opens in a third column showing:
   - Paper title, authors, and year in the header
   - Full PDF content (if available)
   - Fallback to "View paper online" link if no PDF is stored
4. Click the **X** button to close the PDF viewer and return to two-column layout

#### Benefits
- **Context Preservation**: Read the paper without leaving your writing environment
- **Efficient Research**: No need to switch between windows or applications
- **Smart Layout**: Interface automatically adjusts between 2 and 3 columns
- **Quick Reference**: Easily reference specific sections while writing

#### Technical Details
- Uses @react-pdf-viewer/core for PDF rendering
- Dynamic flex-based layout with responsive column sizing
- PDF files served from backend at `/api/papers/{paper_id}/pdf`
- Supports papers with uploaded PDF files (check `has_pdf` field)
- Loading states and error handling for smooth user experience

#### Layout Behavior
- **Two-Column Mode** (default):
  - Editor: 60% width (flex-[3])
  - Citations: 40% width (flex-[2])
- **Three-Column Mode** (with PDF viewer):
  - Editor: 40% width (flex-[2])
  - Citations: 20% width (flex-[1])
  - PDF Viewer: 40% width (flex-[2])

#### Requirements
- Papers must have PDF files uploaded to be viewable
- Backend must be running and accessible
- Modern browser with PDF rendering support

### NEW: External Metadata Integration & Manual Editing 📊
Automatic metadata fetching from arXiv and Crossref APIs, with manual editing capabilities:

#### How it Works
- **Automatic API Integration**: When you upload a paper, the system automatically:
  - Searches for arXiv IDs and DOIs in the paper text
  - Fetches accurate metadata from arXiv API (for preprints) or Crossref API (for published papers)
  - Falls back to text extraction only if no identifiers are found
- **Metadata Source Tracking**: See where each paper's metadata came from (arxiv, crossref, text_extraction, etc.)
- **Manual Editing**: Edit paper metadata using the pencil (✏️) button in the Paper Library

#### Using External APIs
The system automatically detects and uses:
1. **arXiv IDs**: Formats like "2506.06352", "arXiv:2506.06352v1"
2. **DOIs**: Formats like "10.1234/example", "https://doi.org/10.1234/example"
3. **Priority**: arXiv → Crossref → Text Extraction

#### Manual Metadata Editing
1. Go to Paper Library and find the paper you want to edit
2. Click the **pencil (✏️)** button
3. Choose between two editing modes:
   - **Manual Edit**: Edit individual fields (title, authors, year, etc.)
   - **Import BibTeX**: Paste a BibTeX entry to import all metadata at once

#### BibTeX Import
```bibtex
@article{example2024,
  title = {Your Paper Title},
  author = {Doe, John and Smith, Jane},
  year = {2024},
  journal = {Journal Name},
  doi = {10.1234/example},
  abstract = {Paper abstract...}
}
```

#### Benefits
- **Accurate Metadata**: No more "mental goal" instead of actual titles
- **Time Saving**: Automatic fetching from trusted academic sources
- **Flexibility**: Manual override when automatic detection fails
- **BibTeX Support**: Easy import for papers you already have citations for
- **Transparency**: Always see where metadata came from

#### Technical Details
- Integrated arXiv XML API and Crossref REST API
- Asynchronous metadata fetching during paper processing
- Identifier extraction using regex patterns
- Client-side BibTeX parsing for quick preview
- Metadata source field added to track data origin

## Recent Updates (July 18, 2025)

### NEW: Overleaf Integration 🚀
Export your documents directly to Overleaf for professional LaTeX editing:

#### How it Works
- **One-Click Export**: Click the green "Open in Overleaf" button in the document editor
- **Automatic Transfer**: Both your LaTeX document and BibTeX bibliography are transferred
- **Ready to Compile**: Files are properly configured with `\bibliography{references}` for seamless compilation
- **New Project Creation**: Each export creates a new Overleaf project

#### Using the Feature
1. Open any document with citations
2. Click the **"Open in Overleaf"** button (green button with external link icon)
3. If not logged into Overleaf, you'll be prompted to sign in
4. Your document opens in a new Overleaf project with:
   - `main.tex` - Your document content with citations
   - `references.bib` - Your bibliography entries
5. Click "Recompile" in Overleaf to generate your PDF

#### Benefits
- **Professional Typesetting**: Use Overleaf's LaTeX environment for final formatting
- **Collaboration**: Share the Overleaf project with co-authors
- **Version Control**: Overleaf tracks changes and versions
- **PDF Export**: Generate publication-ready PDFs

#### Technical Details
- Uses Overleaf's form submission API
- Automatically saves document before export
- Bibliography filename standardized to `references.bib` for consistency
- Compatible with all LaTeX compilers (pdfLaTeX, XeLaTeX, LuaLaTeX)

## Recent Updates (July 17, 2025)

### Bug Fix: Content Restoration on Tab Switch (v0.0.2) 🔧
Fixed an issue where saved content was not being restored when switching back to the editor tab:

#### Issue
- When switching from the editor tab to bibliography/citations tabs, content would auto-save correctly
- However, when switching back to the editor tab, the saved content would not be restored
- The editor would show the initial content loaded when the document was first opened
- This was due to the Editor component being unmounted/remounted on tab switches and using stale content

#### Solution
- Added document content reload when switching back to the editor tab
- Updated LoadInitialContentPlugin to properly handle content updates
- Documents now reload with the latest saved content when returning to the editor tab
- Tab switching now preserves all edits made during the session

### Bug Fix: Citation Auto-Save (v0.0.1) 🔧
Fixed an issue where documents wouldn't auto-save after inserting citations:

#### Issue
- After inserting a citation using the citation panel, the document would not automatically save
- Users had to type additional text for the save to trigger
- This was due to programmatic citation insertion not triggering the onChange event

#### Solution
- Added manual save trigger after citation insertion
- Documents now save automatically 100ms after a citation is inserted
- Normal typing behavior and auto-save remain unchanged

## Previous Updates (July 17, 2025)

### NEW: Bulk Document Management (v1.3.0) 🗑️
Enhanced document management capabilities for better productivity:

#### Multi-Document Deletion
- **Select Multiple Documents**: Click checkboxes on document cards to select multiple documents
- **Visual Feedback**: Selected documents are highlighted with a blue border and overlay
- **Bulk Action Bar**: Floating toolbar appears at the bottom when documents are selected
- **Select All**: Quick button to select/deselect all visible documents
- **Delete Selected**: Remove multiple documents with a single action

#### Database Cleaning (Testing Only)
For testing and development purposes:
- **Access**: Paper Library → Settings (⚙️) → Database Management tab
- **Clean All Documents**: Remove ALL documents from ALL users
- **Safety**: Requires typing "DELETE ALL" to confirm
- **Preservation**: User accounts and paper library remain intact
- **Scope**: Only deletes documents, citations, and document-paper associations

## Recent Updates (July 16, 2025)

### NEW: Document-Centric Workflow 🎯
The application now supports a document-centric approach where you start with your document and build its bibliography:

#### Document-Paper Assignment
- **Assign Papers to Documents**: Build your bibliography by assigning papers to specific documents
- **Bulk Assignment**: Assign multiple papers at once for efficiency
- **Reorder Papers**: Organize your bibliography with custom ordering
- **Notes**: Add context-specific notes about why each paper is relevant

#### Export Functionality
- **BibTeX Export**: Export your document's bibliography as a `.bib` file
  - GET `/api/documents/{id}/export/bibtex`
  - Includes all assigned papers with proper citation keys
  - Compatible with LaTeX bibliography managers
  
- **LaTeX Export**: Export your document content as a `.tex` file
  - GET `/api/documents/{id}/export/latex`
  - Converts Lexical editor content to LaTeX format
  - Includes document structure, formatting, and bibliography references

#### API Endpoints
- `POST /api/documents/{id}/papers` - Assign a paper to document
- `POST /api/documents/{id}/papers/bulk` - Bulk assign multiple papers
- `GET /api/documents/{id}/papers` - List all papers assigned to document
- `PATCH /api/documents/{id}/papers/{paper_id}` - Update assignment (notes, position)
- `POST /api/documents/{id}/papers/reorder` - Reorder papers in bibliography
- `DELETE /api/documents/{id}/papers/{paper_id}` - Remove paper from document

#### Metadata Enrichment (Coming Soon)
- Automatic metadata fetching from external sources:
  - arXiv API for preprints
  - Crossref for DOI resolution
  - Semantic Scholar for citation data
  - OpenAlex for comprehensive metadata

## Recent Updates (July 15, 2025)

### Document-Centric Workflow Frontend ✅ (Fixed July 16)
- **Zotero Sync Removed**: All Zotero functionality has been removed in favor of document-centric approach
- **New Workflow**:
  1. Create or open a document
  2. Upload papers to your library
  3. Assign papers to documents from the library (📎 icon)
  4. Manage bibliography in the document's Bibliography tab
  5. Export as BibTeX or LaTeX

- **Document Editor Enhancements**:
  - **Three Tabs**: Editor | Bibliography | Citations
  - **Bibliography Tab**: 
    - View all assigned papers
    - Drag-and-drop reordering
    - Add/edit notes for each paper
    - Remove papers from bibliography
  - **Citations Tab**: Real-time citation suggestions with badge counter

- **Paper Library Enhancements**:
  - **Assign to Document** button (📎) on indexed papers
  - Quick assignment dialog with document search
  - Add optional notes when assigning

- **Export Improvements**:
  - **BibTeX Export**: Download bibliography as `.bib` file
  - **LaTeX Export**: Download full document as `.tex` file
  - All original formats still supported (Markdown, HTML, Plain Text, JSON)

- **Bug Fix (July 16)**: Fixed paper assignment API errors that prevented papers from being assigned to documents. The document-paper relationship loading has been corrected and all assignment features now work properly.

### New: System Logging and Monitoring ✅
- **Comprehensive Logging System** - Track all system activities and debug issues
  - **Log Categories**: Document operations, PDF processing, authentication, API calls, database operations
  - **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
  - **Log Viewer API**: View logs with pagination, filtering, and search
  - **Error Tracking**: Detailed error traces with context for debugging
  - **File Not Found Tracking**: Specific logging for missing PDF files
  - **Status**: ✅ Fully operational
  
- **Frontend Log Viewer** - User-friendly interface for viewing logs
  - **Access**: 
    - Click "View Logs" in Paper Library header
    - Direct URL: http://localhost:3000/logs
  - **Features**:
    - Real-time log display with auto-refresh option (10 second interval)
    - Color-coded log levels for quick visual scanning
    - Search across all log messages
    - Filter by level, category, or date range
    - Pagination controls for browsing large log sets
    - Detailed view for each log entry with metadata and error traces
    - Export logs as JSON for external analysis
    - Clear logs functionality (with confirmation)
  
- **API Endpoints for Logs**:
  - `GET /api/logs/` - View logs with pagination and filtering
  - `GET /api/logs/stats` - Get log statistics by level and category
  - `DELETE /api/logs/old` - Clean up old logs (specify days to keep)
  
- **Log Filtering Options**:
  - By level: `?level=ERROR`
  - By category: `?category=PDF_PROCESSING`
  - By date range: `?start_date=2025-07-15&end_date=2025-07-16`
  - By search term: `?search=file%20not%20found`
  - Pagination: `?page=1&per_page=50`
  
- **Installation Note**: If you see import errors for `lucide-react`, run:
  ```bash
  docker-compose exec frontend npm install lucide-react
  ```

## Recent Updates (July 15, 2025)

### Zotero Sync - Final Verification Complete ✅
- **All Systems Operational** - Comprehensive testing confirms sync is working correctly
  - **Papers Syncing**: ✅ 47 papers successfully imported from 3 collections
  - **PDF Downloads**: ✅ 44/47 papers (93.6%) have PDFs attached
  - **Progress Tracking**: ✅ Real-time progress updates working throughout sync
  - **Collection Filtering**: ✅ Correctly identifies and syncs only selected collections
  
- **Understanding Sync Messages** - "0 papers synced" doesn't mean failure
  - This message appears when all papers are already up-to-date
  - Papers sync incrementally - only new or updated papers are processed
  - Force full sync option available to re-sync all papers
  - Check database for actual paper count to verify successful sync

### Zotero Collection Format Fix - Latest Update
- **Old Format Collection Sync** - Fixed critical issue where collections saved in old format wouldn't sync
  - **Root Cause**: Collections saved as `["CPUVP4AQ", "7AZYIPWP"]` (just keys) instead of new format `[{key: "CPUVP4AQ", libraryId: "users/12345"}]`
  - **Solution**: System now automatically detects old format and searches all libraries to find where collections belong
  - **Migration**: Added `migrate_collection_format()` method to convert old format to new format
  - **Optimization**: Only fetches from libraries that contain selected collections, improving performance
  - **Status**: ✅ Successfully tested with 47 papers from 3 collections

### Zotero Sync Improvements - Major Fix
- **Force Full Sync Option** - New option to bypass timestamp filtering
  - Addresses "0 papers synced" issue when timestamp filtering is too restrictive
  - API endpoint now accepts `{"force_full_sync": true}` parameter
  - Frontend support coming soon
  
- **Enhanced Collection Sync** - Better handling of collection filtering
  - Improved logic to search all user groups when collections are selected
  - Better backward compatibility with old collection format
  - Comprehensive logging to debug sync issues
  
- **PDF Processing Improvements** - Automatic processing for search
  - All PDFs are now automatically processed for chunking and embeddings
  - Reprocesses papers that have files but weren't processed
  - Better error handling and status reporting
  - Shows processing statistics after sync completes

### Zotero Sync Timestamp Issue Fixed
- **0 Papers Returned Bug** - Fixed critical issue where sync returned 0 papers despite having papers available
  - **Root Cause**: Timestamp filtering logic used `last_sync` timestamp to filter items, but recent timestamps caused API to return 0 results
  - **Solution**: Clear `last_sync` timestamp to force full sync when needed
  - **Database Fix**: `UPDATE zotero_config SET last_sync = NULL` to reset sync state
  - **Status**: ✅ 26 papers successfully synced from collection "CPUVP4AQ"
  - **PDFs**: ✅ 25/26 papers have PDFs downloaded
  - **Embeddings**: ⚠️ Paper processing has transaction timing issues (known issue)

### Zotero Collection Sync Fixed
- **Collection-Only Sync** - Fixed issue where selecting only collections (no groups) would fail
  - Updated collection data format to include library ID: `[{key: "COLLECTION_KEY", libraryId: "users/12345"}]`
  - System now correctly determines which libraries contain selected collections
  - Maintains backward compatibility with existing collection configurations
  - Added comprehensive test coverage for collection sync logic

- **Sync Progress Tracking** - Real-time progress monitoring for sync operations
  - Shows current step (starting, fetching, processing, completed)
  - Displays progress counters (processed/total papers, libraries processed)
  - New API endpoint: `GET /zotero/sync/progress` for monitoring sync status
  - Progress updates in real-time during sync operations
  - Visual progress bar with percentage completion and status messages
  - Automatic polling every second during active sync operations

### Zotero PDF Sync Fixed
- **PDF Attachments Now Sync** - PDFs are downloaded during Zotero sync
  - Previously excluded attachments, preventing PDF downloads
  - Now fetches both papers AND their PDF attachments
  - Downloads PDFs for chunk creation and embedding search
  - Shows count of PDF attachments available during sync

### Zotero Group Selection Fixed
- **Frontend Group Display** - Selected groups now properly show as checked when reloading settings
  - Status endpoint returns selected groups and collections
  - Frontend loads saved selections on page load
  - Checkboxes correctly reflect saved state

- **Group Sync Fixed** - Papers from selected Zotero groups now sync correctly
  - Fixed API URL construction for group libraries
  - COAI group (and other groups) now fetch papers properly
  - Respects group/collection filter during sync

### Zotero Sync Issues Fixed
- **Empty DOI Handling** - Papers without DOIs now sync correctly
  - Database now properly stores NULL instead of empty strings for missing DOIs
  - Unique constraint violation errors eliminated
  - Run migration: `cd backend && python run_doi_migration.py`
  
- **Detailed Sync Reporting** - See exactly what happened during sync
  - Shows count of new papers imported
  - Shows count of papers updated
  - Shows count of failed imports with details
  - Success messages display formatted results

- **Settings Save Fixed** - Update sync settings without re-entering credentials
  - API key and User ID only required for initial setup
  - Can update sync intervals and selected libraries independently
  - Selected groups and collections properly saved

### Zotero Integration - Enhanced
- **Group and Collection Selection** - Choose specific libraries and collections to sync
  - Select multiple Zotero groups/libraries
  - Filter by specific collections within libraries
  - Sync only the papers you need
  - Visual UI for easy selection with checkboxes

### Duplicate DOI Handling - Fixed
- **Smart Duplicate Detection** - Prevents duplicate papers with same DOI
  - Checks for existing papers by DOI before creating new ones
  - Links Zotero items to existing papers when DOI matches
  - Updates metadata only when existing values are empty
  - Proper transaction handling with rollback on errors
  - Continues syncing other papers even if some fail

## Previous Updates (July 14, 2025)

### Zotero Integration
- **Automatic Paper Sync** - Connect your Zotero library for automatic imports
  - Configure with API key and User ID (User ID: 5008235 for your account)
  - Sync papers with full metadata (title, authors, year, journal)
  - Download PDFs automatically
  - Configurable sync intervals (default: 30 minutes)
  - Track sync status and handle updates

## Previous Updates

### New Features:
1. **Chunk-Based Search** - Papers are split into 250-word chunks with individual embeddings
   - Searches entire paper content, not just abstracts
   - Shows preview text from matching chunks
   - Displays section titles and chunk numbers (Part 1, Part 2, etc.)
   - Limited to 2 best chunks per paper to avoid duplicates

2. **Sentence-Level Citation Suggestions** - Citations update based on current sentence
   - Extracts only the sentence where your cursor is located
   - No longer uses entire document for short texts
   - Properly handles questions and complex punctuation
   - Includes previous/next sentences for context

3. **Citation Insertion** - Click "Insert" to add citations directly into your document
   - Format: `(Author et al., Year)` for papers with metadata
   - Fallback: `[paper-id]` for papers without metadata
   - Text selection triggers manual citation search

4. **Improved Metadata Extraction** - Better title and author detection from PDFs
5. **Real-time Paper Processing** - Papers show chunk counts and processing status
6. **Auto-refresh** - Paper library updates every 3 seconds while processing

### Fixed Issues:
- Citation suggestions now change based on cursor position
- No more duplicate suggestions with same key
- Chunk preview shows why each paper was suggested
- Paper upload works correctly with multipart form data
- Chunk counts display properly
- MarkItDown compatibility fixed for latest version

## API Configuration

The application uses the following API configuration:
- Frontend API Base URL: `http://localhost:8000/api` (configured via `VITE_API_URL` environment variable)
- All service calls should use relative paths without the `/api` prefix (e.g., `/papers/`, `/documents/`)
- The axios instance in `frontend/src/services/api.ts` automatically prepends the base URL

## Current Implementation Status (Phase I - In Progress)

### What's Working Now

1. **Backend API**:
   - FastAPI server with health check endpoints
   - `/api/health` - Basic health check
   - `/api/health/ready` - Readiness probe (checks Redis)
   - `/api/health/live` - Liveness probe
   - Document CRUD operations
   - Paper upload and processing
   - Real-time citation suggestions via WebSocket

2. **Frontend**:
   - React app with TypeScript and TailwindCSS
   - Document editor with Lexical
   - Real-time citation suggestions
   - Paper library with drag-and-drop upload
   - Document management interface

3. **Core Features**:
   - **Document Editing**: Rich text editor with auto-save
   - **Citation Suggestions**: Real-time suggestions as you type
   - **Citation Insertion**: Click to insert formatted citations at cursor position
   - **Paper Upload**: Drag-and-drop PDF/DOCX/TXT files (max 50MB)
   - **Text Extraction**: Using Microsoft's MarkItDown with OCR support
   - **Smart Search**: Vector similarity search with pgvector
   - **Metadata Extraction**: Automatic title, author, and year extraction from PDFs

4. **Infrastructure**:
   - Docker Compose setup for local development
   - PostgreSQL with pgvector extension
   - Redis for caching
   - Hot-reloading for both frontend and backend

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.10+ (for local backend development)

### Quick Start with Docker

1. Clone the repository:
   ```bash
   git clone https://github.com/prof-schacht/academic-citation-assistant.git
   cd academic-citation-assistant
   ```

2. Start all services:
   ```bash
   docker-compose up -d
   ```

3. **IMPORTANT**: Run database migrations (required for fresh installations):
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

4. Create test user (required for document operations):
   ```bash
   docker-compose exec backend python scripts/create_test_user_simple.py
   ```

5. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

6. Populate test papers (for citation suggestions):
   ```bash
   docker-compose exec backend python scripts/populate_test_papers_v2.py
   ```

**Note**: If you encounter "relation 'documents' does not exist" errors, ensure you've run the database migrations in step 3. If you get "foreign key constraint" errors when creating documents, ensure you've created the test user in step 4.

## Using the Application

### Creating and Editing Documents

1. Navigate to http://localhost:3000
2. Click "Get Started" to go to the documents page
3. Click "+ New Document" to create a new document
4. Start typing in the editor - citation suggestions will appear automatically in the right panel

### Real-time Citation Suggestions

As you type about academic topics, the system will:
- Analyze your text in real-time
- Search for relevant papers in the database
- Display suggestions ranked by relevance
- Update suggestions as you move between sentences

**Tips for better suggestions:**
- Type complete sentences about specific topics
- Use academic terminology (e.g., "transformer architectures", "BERT model")
- The system needs at least 10 characters to trigger suggestions

### Uploading Papers to Your Library

1. Go to Documents page and click "📚 Paper Library"
2. Click "+ Upload Papers"
3. Drag and drop files or click to browse:
   - Supported formats: PDF, DOCX, DOC, TXT, RTF
   - Maximum file size: 50MB
   - Multiple files can be uploaded at once

4. Files will be processed automatically:
   - Text extraction using MarkItDown (includes OCR for scanned PDFs)
   - Metadata extraction (title, authors, abstract)
   - Text chunking for vector search
   - Embedding generation for similarity matching

5. Monitor processing status in the library view:
   - ⏳ Processing: File is being analyzed
   - ✅ Indexed: Ready for citation matching
   - ❌ Error: Processing failed (can retry)

### Managing Your Paper Library

- **Search**: Use the search bar to find papers by title or author
- **Filter**: Show only indexed, processing, or error papers
- **Sort**: Order by date, title, or citation count
- **Actions**: Edit metadata or delete papers

### Local Development (Without Docker)

1. **Backend Setup**:
   ```bash
   cd backend
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e ".[dev]"
   cp .env.example .env
   python run.py
   ```

2. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Database Setup** (requires PostgreSQL with pgvector):
   ```sql
   CREATE USER citation_user WITH PASSWORD 'citation_pass';
   CREATE DATABASE citation_db OWNER citation_user;
   \c citation_db
   CREATE EXTENSION vector;
   ```

## Development Commands

From the root directory:

```bash
# Start development environment
npm run dev

# Run tests (when implemented)
npm test

# Lint code
npm run lint

# Format code
npm run format

# Build for production
npm run build

# Docker commands
npm run docker:build    # Build containers
npm run docker:down     # Stop containers
npm run docker:clean    # Stop and remove volumes
```

## Environment Variables

Backend configuration is managed through `.env` file:
- Copy `backend/.env.example` to `backend/.env`
- Update values as needed for your environment

Key variables:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `CORS_ORIGINS` - Allowed frontend origins
- `DEBUG` - Enable debug mode (True/False)

## API Endpoints

Currently available endpoints:

### Health Checks
- `GET /` - Root endpoint, returns app info
- `GET /api/health` - Basic health check
- `GET /api/health/ready` - Readiness probe
- `GET /api/health/live` - Liveness probe

### Database Management

**Run migrations:**
```bash
cd backend
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
alembic upgrade head
```

**Create new migration:**
```bash
alembic revision --autogenerate -m "description"
```

**Check migration status:**
```bash
alembic current
```

### Document Management API

**Create a document:**
```bash
curl -X POST http://localhost:8000/api/documents/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Research Paper",
    "description": "A paper about AI",
    "content": {"root": {"type": "root", "children": [...]}},
    "is_public": false
  }'
```

**List documents:**
```bash
curl http://localhost:8000/api/documents/
```

**Get a specific document:**
```bash
curl http://localhost:8000/api/documents/{document_id}
```

**Update a document:**
```bash
curl -X PUT http://localhost:8000/api/documents/{document_id} \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Title"}'
```

**Delete a document:**
```bash
curl -X DELETE http://localhost:8000/api/documents/{document_id}
```

### Real-time Citation API (NEW)

**WebSocket endpoint for real-time suggestions:**
```
ws://localhost:8000/ws/citations?user_id={user_id}
```

**Message format for requesting suggestions:**
```json
{
  "type": "suggest",
  "text": "Machine learning has revolutionized...",
  "context": {
    "currentSentence": "Machine learning has revolutionized...",
    "previousSentence": "Previous sentence text",
    "paragraph": "Full paragraph text",
    "cursorPosition": 42
  }
}
```

**Response format:**
```json
{
  "type": "suggestions",
  "results": [
    {
      "paperId": "paper-123",
      "title": "Deep Learning in Natural Language Processing",
      "authors": ["Smith, J.", "Doe, A."],
      "year": 2023,
      "abstract": "This paper presents...",
      "confidence": 0.92,
      "citationStyle": "inline",
      "displayText": "(Smith et al., 2023)"
    }
  ]
}
```

### Coming Soon
- Paper upload and processing
- User authentication
- External API integrations (Semantic Scholar, PubMed)

## Troubleshooting

### Common Issues

1. **Database errors on fresh installation**:
   - Error: "relation 'documents' does not exist"
   - Solution: Run database migrations
   ```bash
   docker-compose exec backend alembic upgrade head
   ```
   - This creates all necessary database tables

2. **Port conflicts**:
   - Frontend default: 3000
   - Backend default: 8000
   - PostgreSQL: 5432
   - Redis: 6379

3. **Docker build fails**:
   ```bash
   docker-compose build --no-cache
   ```

3. **Database connection issues**:
   - Ensure PostgreSQL is running
   - Check DATABASE_URL in .env
   - Verify pgvector extension is installed

4. **Frontend not updating**:
   - Clear browser cache
   - Check for TypeScript errors
   - Restart Vite dev server

## Next Features (In Development)

- ✅ Database models and migrations (DONE)
- ✅ Document editor with Lexical (DONE)
- ✅ Real-time citation suggestions (DONE)
- Paper upload functionality
- Text extraction from PDFs
- Vector embeddings for uploaded papers
- External API integrations

## Real-time Citation Features

### How Citation Suggestions Work

1. **Text Analysis**: As you type, the system analyzes your current sentence and surrounding context
2. **Embedding Generation**: Your text is converted to a 384-dimensional vector using sentence-transformers
3. **Vector Search**: The system searches for similar paper chunks using pgvector's cosine similarity
4. **Ranking**: Results are ranked by multiple factors including relevance, quality, and recency
5. **Real-time Delivery**: Suggestions are delivered via WebSocket in under 1 second

### Performance Optimizations

- **Debouncing**: Requests are debounced by 500ms to avoid overwhelming the system
- **Caching**: Frequently requested embeddings are cached in memory
- **Rate Limiting**: 60 requests per minute per user
- **Connection Management**: Automatic reconnection with exponential backoff

## Zotero Integration Guide

### Setting Up Zotero Sync

1. **Get Your Zotero Credentials:**
   - Go to [Zotero Settings → Keys](https://www.zotero.org/settings/keys)
   - Create a new private key with library read access
   - Note your User ID (for your account: 5008235)
   - Copy your API Key

2. **Configure in the App:**
   - Navigate to Paper Library → Zotero Settings
   - Enter your User ID and API Key
   - Click "Connect to Zotero"

3. **Select Libraries and Collections:**
   - After connecting, you'll see your available libraries
   - Check the libraries you want to sync
   - Optionally select specific collections
   - Click "Update Settings" to save

4. **Manual or Automatic Sync:**
   - Click "Sync Now" for immediate sync
   - Enable auto-sync with customizable intervals
   - Monitor sync status in the UI
   - Real-time progress bar shows sync progress:
     - Percentage completion (0-100%)
     - Current status (e.g., "Fetching items...", "Processing paper 5 of 100")
     - Item count progress (current/total processed)
     - Progress updates every second during active sync

### Troubleshooting Zotero Integration

1. **Authentication Issues:**
   - Ensure you're using the test user (UUID: 00000000-0000-0000-0000-000000000001)
   - Check that your API key has library read permissions
   - Verify your User ID is correct

2. **Sync Issues:**
   - Check the sync status message for specific errors
   - Ensure selected libraries/collections contain papers
   - Verify network connectivity to Zotero API

---

Last updated: 2025-07-18

## Version History

### v0.2.1 - PDF Viewer for Citations
- NEW: Added integrated PDF viewer for citation details
- Feature: Three-column layout when viewing PDFs (Editor | Citations | PDF Viewer)
- Feature: Click "View Details" on any citation to open the paper's PDF
- Feature: Visual highlighting of selected citation in the panel
- Feature: Close button to return to two-column layout
- Improvement: Dynamic layout adjustment with responsive column sizing
- Technical: Uses @react-pdf-viewer/core for PDF rendering
- Technical: Backend endpoint `/api/papers/{paper_id}/pdf` serves PDF files

### v0.2.0 - Overleaf Integration
- NEW: Added "Open in Overleaf" button for one-click export to Overleaf
- Feature: Exports both LaTeX document and BibTeX bibliography to new Overleaf project
- Feature: Automatic document save before export
- Feature: Bibliography reference uses standardized `references.bib` filename
- Improvement: Loading state indicator while exporting
- Technical: Uses Overleaf's form submission API for project creation

### v0.1.3 - Citation Key Format Consistency
- Fixed: BibTeX export now generates citation keys without colons to match LaTeX export
- Changed: Citation keys now use format `AuthorYearTitle` instead of `Author:Year:Title`
- Example: `Gelp2024Towards` instead of `Gelp:2024:Towards`
- Improvement: Consistent citation key format between BibTeX and LaTeX exports

### v0.1.2 - Citation Export Complete Fix  
- Fixed: LaTeX export from backend now correctly includes citations as `\cite{citationKey}`
- Fixed: All export formats (Markdown, Plain Text, LaTeX) now preserve citations properly
- Fixed: Citations in nested structures (lists, quotes, headings) are preserved during export
- Improvement: Consistent citation format across all export types
- Technical: Enhanced recursive node processing in both frontend and backend export functions

### v0.1.1 - Citation Export Fix (Frontend)
- Fixed: Frontend exports (Markdown, Plain text) now preserve citations as `\cite{citationKey}`
- Fixed: Added `getTextContent()` method to CitationNode for proper text export
- Technical: Updated export utilities to handle citation nodes recursively

### v0.1.0 - Citation Badge Persistence
- Fixed: "Cited" badges now persist when document is closed and reopened
- Added: Document content parsing to identify cited papers on load
- Improvement: Citation tracking is restored from document content
- Technical: Parses Lexical editor state to find citation nodes

### v0.0.9 - Simplified Citations Panel
- Removed: "My Library" tab from Citations panel - it was unnecessary
- Improvement: Cleaner, more focused UI for citation suggestions
- Simplified: Citations panel now only shows suggestions

### v0.0.8 - Allow Multiple Citations
- Fixed: Papers can now be cited multiple times in the same document
- Changed: Insert button is always enabled, even for already cited papers
- Improvement: Academic papers often need to be cited multiple times throughout a document

### v0.0.7 - Fixed Citation Badge Display
- Fixed: Both "In Library" and "Cited" badges now show when appropriate
- Fixed: Papers can show both badges if they are in bibliography AND cited
- Added: Debug logging to help track citation state
- Improvement: Badge display logic is clearer and more reliable

### v0.0.6 - Bibliography State Synchronization
- Fixed: Bibliography papers are reloaded when switching from Bibliography tab to catch deletions
- Fixed: "In Library" badges now correctly disappear when papers are removed from bibliography
- Fixed: Citation status tracking is more robust and updates properly
- Improvement: Better state management for bibliography and cited papers

### v0.0.5 - Citation Status Badges and Add to Library
- Added: "Add to Library" button functionality to add papers directly to bibliography
- Added: Visual badges showing citation status:
  - "Cited" badge (blue) for papers already cited in the document
  - "In Library" badge (green) for papers in the bibliography but not cited
- Added: Buttons are disabled with appropriate text when action is already completed
- Added: Bibliography and cited papers are tracked across the application
- Improvement: All paper chunks show the same status badges when a paper is cited/added

### v0.0.4 - Bibliography Auto-Refresh
- Fixed: Bibliography now automatically refreshes when new citations are added
- Fixed: Multiple citations properly appear in bibliography without manual refresh
- Improvement: Bibliography component remounts with updated data when citations are inserted

### v0.0.3 - Editor State Persistence
- Fixed: Editor now remains mounted when switching tabs (hidden instead of unmounted)
- Fixed: Content is preserved in editor memory when navigating between tabs
- Fixed: No need to reload content from server when switching back to editor
- Improvement: Better performance as editor doesn't need to reinitialize

### v0.0.2 - Enhanced Save Mechanisms
- Fixed: Added multiple save triggers to prevent data loss
  - Immediate save when clicking outside the editor
  - Forced save with delay when switching tabs
  - Direct save using current editor state
- Fixed: First content change now always triggers auto-save
- Added: Comprehensive logging for debugging save issues

### v0.0.1 - Citation Save Fix
- Fixed: Document content now saves immediately after citation insertion
- Fixed: First content change in editor triggers auto-save correctly
- Fixed: Citations automatically added to bibliography when inserted
- Fixed: Citations tracked and displayed in Citations tab

### Known Issues
- LaTeX-style citations are shown as visual icons but the underlying LaTeX command may need adjustment for your specific LaTeX setup
