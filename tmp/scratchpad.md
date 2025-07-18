# Academic Citation Assistant - Development Scratchpad

## External Metadata Integration Development

### Date: 2025-07-18

#### Problem Statement
The metadata extraction from uploaded PDFs was producing poor quality results. For example, instead of extracting the actual paper title, it was extracting phrases like "mental goal" from the text. The user requested integration with external APIs (arXiv, DOI) to fetch accurate metadata.

#### Solution Implemented

1. **External API Research**
   - Created comprehensive documentation of available APIs (arXiv, Crossref, Semantic Scholar, PubMed)
   - Documented rate limits, authentication requirements, and response formats

2. **External Metadata Service**
   - Created `external_metadata_service.py` with three main components:
     - `ArxivClient`: Fetches metadata from arXiv API using XML format
     - `CrossrefClient`: Fetches metadata from Crossref API using DOI
     - `MetadataFetcherService`: Unified service that coordinates fetching from multiple sources
   - Added identifier extraction from text (arXiv IDs, DOIs, PMIDs)
   - Implemented BibTeX parsing for manual metadata entry

3. **Backend Integration**
   - Updated `paper_processor.py` to use external APIs before falling back to text extraction
   - Added `metadata_source` field to Paper model to track where metadata came from
   - Updated API response schema to include metadata source

4. **Frontend Manual Editing**
   - Created `PaperMetadataEditor` component with two modes:
     - Manual form editing for individual fields
     - BibTeX import for bulk metadata entry
   - Integrated edit button in Paper Library page
   - Shows metadata source to users

5. **Testing**
   - Created comprehensive unit tests for external metadata service
   - Tests cover ID cleaning, metadata extraction, API mocking, and fallback logic

#### Technical Decisions
- Used httpx for async HTTP requests in Python
- Implemented fallback strategy: arXiv → Crossref → text extraction
- Simple client-side BibTeX parsing (could be improved with backend endpoint)
- Kept external API calls in background processing to avoid blocking uploads

#### Next Steps
- Add Semantic Scholar API integration
- Implement server-side BibTeX parsing endpoint
- Add retry logic for failed API calls
- Consider caching external API responses
- Add manual override for auto-detected identifiers
