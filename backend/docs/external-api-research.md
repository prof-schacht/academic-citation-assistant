# Academic Metadata APIs Research

This document provides comprehensive information about free academic metadata APIs for fetching paper information.

## 1. arXiv API

### Overview
The arXiv API provides programmatic access to arXiv's metadata using the Atom 1.0 XML format.

### API Details
- **Base URL**: `http://export.arxiv.org/api/query`
- **Authentication**: None required
- **Response Format**: Atom 1.0 XML
- **Rate Limits**: 
  - Maximum 30,000 results per call
  - Recommended slice size: 2,000 results
  - Suggested 3-second delay between calls

### Fetching by arXiv ID
To fetch metadata for a specific arXiv ID (e.g., "2506.06352v1"):
```
http://export.arxiv.org/api/query?id_list=2506.06352v1
```

### Response Fields
- `<title>`: Article title
- `<id>`: Abstract page URL
- `<summary>`: Article abstract
- `<author>`: Author information (with optional affiliations)
- `<published>`: First submission date
- `<updated>`: Latest version submission date
- `<category>`: Subject categories
- `<link>`: Links to abstract, PDF, and DOI (when available)

### Example Code
```python
import urllib.request
import xml.etree.ElementTree as ET

# Fetch metadata for arXiv ID
arxiv_id = "2506.06352v1"
url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"

response = urllib.request.urlopen(url)
xml_data = response.read().decode('utf-8')

# Parse XML
root = ET.fromstring(xml_data)
# Extract metadata from the XML structure
```

### Documentation
- User Manual: https://info.arxiv.org/help/api/user-manual.html
- API Basics: https://info.arxiv.org/help/api/basics.html

## 2. Crossref API

### Overview
Crossref's REST API provides access to metadata for works registered with DOIs, including bibliographic metadata, funding data, license information, full-text links, ORCID iDs, and abstracts.

### API Details
- **Base URL**: `https://api.crossref.org`
- **Authentication**: None required (but email in headers recommended for "polite" pool)
- **Response Format**: JSON
- **Rate Limits**: Advertised in `X-Rate-Limit-Limit` and `X-Rate-Limit-Interval` headers

### Fetching by DOI
To fetch metadata for a specific DOI:
```
https://api.crossref.org/works/{DOI}
```

Example:
```
https://api.crossref.org/works/10.5555/487hjd
```

### Response Fields
- Bibliographic metadata (title, authors, publication date, etc.)
- Funding data
- License information
- Full-text links
- ORCID iDs
- Abstracts
- Crossmark updates

### Best Practices
- Include email in headers for priority processing: `User-Agent: YourApp/1.0 (mailto:you@example.com)`
- Use `select` parameter for specific fields: `/works?rows=10&select=DOI,title,author`
- Batch requests: Use filter parameter for multiple DOIs (max 100 recommended)
- Default results: 20, maximum: 1,000 per request

### Example Code
```python
import requests

# Fetch metadata for DOI
doi = "10.1038/nature12373"
url = f"https://api.crossref.org/works/{doi}"

headers = {
    'User-Agent': 'YourApp/1.0 (mailto:your.email@example.com)'
}

response = requests.get(url, headers=headers)
metadata = response.json()
```

### Documentation
- REST API: https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- GitHub: https://github.com/CrossRef/rest-api-doc
- Swagger UI: https://api.crossref.org/swagger-ui/index.html

## 3. Semantic Scholar API

### Overview
The Semantic Scholar Academic Graph API provides access to a comprehensive database of academic papers with enhanced metadata including abstracts, citations, and semantic analysis.

### API Details
- **Base URL**: `http://api.semanticscholar.org/graph/v1/`
- **Authentication**: Optional API key (recommended for higher rate limits)
- **Response Format**: JSON
- **Rate Limits**: 
  - Unauthenticated: 1,000 requests/second (shared among all users)
  - Authenticated: 1 request/second (introductory rate)

### Fetching Paper Metadata
Several endpoints available:
- Paper details: `/paper/{paperId}`
- Paper batch: `/paper/batch` (for multiple papers)
- Paper search: `/paper/search/bulk`

Paper IDs can be:
- Semantic Scholar ID
- DOI (with "DOI:" prefix)
- arXiv ID (with "ARXIV:" prefix)
- PubMed ID (with "PMID:" prefix)

### Available Fields
Use the `fields` parameter to specify which data to return:
- Basic: title, authors, year, venue, abstract
- Extended: citations, references, influentialCitationCount, fieldsOfStudy
- Additional: publicationTypes, journal, externalIds, url, openAccessPdf

### Example Code
```python
import requests

# Fetch by DOI
paper_id = "DOI:10.1038/nature12373"
url = f"http://api.semanticscholar.org/graph/v1/paper/{paper_id}"

params = {
    'fields': 'title,authors,year,abstract,venue,externalIds'
}

headers = {
    'x-api-key': 'YOUR_API_KEY'  # Optional but recommended
}

response = requests.get(url, params=params, headers=headers)
metadata = response.json()
```

### Documentation
- API Docs: https://api.semanticscholar.org/api-docs/
- Get API Key: https://www.semanticscholar.org/product/api
- Tutorial: https://www.semanticscholar.org/product/api/tutorial

## 4. PubMed E-utilities API

### Overview
The E-utilities are NCBI's API for accessing PubMed and other Entrez databases, providing programmatic access to biomedical literature metadata.

### API Details
- **Base URL**: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`
- **Authentication**: API key optional but recommended
- **Response Format**: XML (default) or JSON
- **Rate Limits**: 
  - Without API key: 3 requests/second
  - With API key: 10 requests/second

### Key Endpoints for Paper Metadata
1. **ESummary** - Retrieves document summaries:
   ```
   https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={PMID}&retmode=json
   ```

2. **EFetch** - Retrieves full records:
   ```
   https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={PMID}&retmode=xml
   ```

### Example Request
Fetch metadata for PMID 33248227:
```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=33248227&retmode=json&api_key=YOUR_KEY
```

### Response Fields (ESummary)
- Title
- Authors
- Journal
- Publication date
- Volume, Issue, Pages
- DOI
- Abstract (if available)
- PubMed Central ID (if available)

### Example Code
```python
import requests
import json

# Fetch metadata for PMID
pmid = "33248227"
base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
endpoint = "esummary.fcgi"

params = {
    'db': 'pubmed',
    'id': pmid,
    'retmode': 'json',
    'api_key': 'YOUR_API_KEY'  # Optional
}

response = requests.get(base_url + endpoint, params=params)
data = response.json()
```

### Documentation
- E-utilities Documentation: https://www.ncbi.nlm.nih.gov/books/NBK25497/
- API Key Registration: https://www.ncbi.nlm.nih.gov/account/settings/

## 5. Additional Free APIs

### CORE API
- **Base URL**: `https://api.core.ac.uk/v3/`
- **Purpose**: Access to open access research papers
- **Authentication**: API key required (free)
- **Documentation**: https://core.ac.uk/documentation/api/

### Europe PMC API
- **Base URL**: `https://www.ebi.ac.uk/europepmc/webservices/rest/`
- **Purpose**: European life sciences literature
- **Authentication**: None required
- **Documentation**: https://europepmc.org/developers/apis

### DOAJ (Directory of Open Access Journals) API
- **Base URL**: `https://doaj.org/api/v2/`
- **Purpose**: Open access journal articles
- **Authentication**: API key required for some endpoints
- **Documentation**: https://doaj.org/docs/api/

## Summary Comparison

| API | Authentication | Rate Limit | Formats | Best For |
|-----|----------------|------------|---------|----------|
| arXiv | None | 3s delay recommended | XML | Physics, Math, CS papers |
| Crossref | None (email recommended) | Varies | JSON | DOI-based lookups |
| Semantic Scholar | Optional API key | 1-1000 RPS | JSON | Comprehensive metadata |
| PubMed | Optional API key | 3-10 RPS | XML/JSON | Biomedical literature |

## Implementation Recommendations

1. **Use Multiple APIs**: Different APIs have different coverage. Consider fallback strategies.
2. **Cache Results**: Store fetched metadata locally to reduce API calls.
3. **Respect Rate Limits**: Implement proper delays and error handling.
4. **Include User Agent**: Always include descriptive user agent headers.
5. **Handle Errors Gracefully**: APIs may be temporarily unavailable or return incomplete data.