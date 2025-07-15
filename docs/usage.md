# Usage Guide - Academic Citation Assistant

## Recent Updates (July 15, 2025)

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
   docker-compose up
   ```

3. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

4. Populate test papers (for citation suggestions):
   ```bash
   docker-compose exec backend python scripts/populate_test_papers_v2.py
   ```

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

1. **Port conflicts**:
   - Frontend default: 3000
   - Backend default: 8000
   - PostgreSQL: 5432
   - Redis: 6379

2. **Docker build fails**:
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

Last updated: 2025-07-15