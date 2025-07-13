# API Documentation

## Overview

The Academic Citation Assistant API provides programmatic access to citation recommendations, document management, and paper library operations. This RESTful API uses JSON for request and response bodies.

## Authentication

All API requests require authentication using Bearer tokens:

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Obtaining Tokens

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your_password"
}
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "expires_in": 3600
}
```

## Base URL

```
https://api.citation-assistant.com/v1
```

## Rate Limiting

- **Free tier**: 100 requests/hour
- **Pro tier**: 1000 requests/hour
- **Enterprise**: Unlimited

Rate limit headers:
- `X-RateLimit-Limit`: Request limit
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset timestamp

## Endpoints

### Documents

#### List Documents

```http
GET /api/documents
```

Query parameters:
- `page` (integer): Page number (default: 1)
- `limit` (integer): Items per page (default: 20)
- `sort` (string): Sort field (created_at, updated_at, title)
- `order` (string): Sort order (asc, desc)

#### Create Document

```http
POST /api/documents
Content-Type: application/json

{
  "title": "My Research Paper",
  "content": {
    "type": "doc",
    "content": [...]
  }
}
```

#### Update Document

```http
PATCH /api/documents/{document_id}
Content-Type: application/json

{
  "title": "Updated Title",
  "content": {...}
}
```

#### Delete Document

```http
DELETE /api/documents/{document_id}
```

### Citations

#### Get Suggestions

```http
POST /api/citations/suggest
Content-Type: application/json

{
  "text": "Machine learning has revolutionized natural language processing",
  "context": "Previous paragraph text for better context",
  "filters": {
    "year_from": 2020,
    "year_to": 2024,
    "min_citations": 10
  },
  "limit": 5
}
```

Response:
```json
{
  "suggestions": [
    {
      "id": "paper_123",
      "title": "Attention Is All You Need",
      "authors": ["Vaswani et al."],
      "year": 2017,
      "confidence": 0.92,
      "relevance_explanation": "Discusses transformer architecture in NLP",
      "citation_count": 50000
    }
  ]
}
```

#### Insert Citation

```http
POST /api/documents/{document_id}/citations
Content-Type: application/json

{
  "paper_id": "paper_123",
  "position": {
    "paragraph": 3,
    "sentence": 2,
    "offset": 45
  }
}
```

### Paper Library

#### Upload Paper

```http
POST /api/papers/upload
Content-Type: multipart/form-data

{
  "file": <PDF file>,
  "metadata": {
    "title": "Optional title override",
    "authors": "Optional authors",
    "year": 2023
  }
}
```

#### List Papers

```http
GET /api/papers
```

Query parameters:
- `search` (string): Search in title/authors/abstract
- `tag` (string): Filter by tag
- `year` (integer): Filter by year

#### Get Paper Details

```http
GET /api/papers/{paper_id}
```

#### Delete Paper

```http
DELETE /api/papers/{paper_id}
```

### Search

#### Search External Sources (Phase II)

```http
POST /api/search/external
Content-Type: application/json

{
  "query": "transformer models in computer vision",
  "sources": ["semantic_scholar", "arxiv"],
  "filters": {
    "year_from": 2020,
    "fields": ["computer science"]
  }
}
```

### WebSocket API

#### Real-time Suggestions

```javascript
// Connect to WebSocket
const ws = new WebSocket('wss://api.citation-assistant.com/ws');

// Authenticate
ws.send(JSON.stringify({
  type: 'auth',
  token: 'YOUR_ACCESS_TOKEN'
}));

// Request suggestions
ws.send(JSON.stringify({
  type: 'suggest',
  text: 'Current sentence being typed',
  documentId: 'doc_123'
}));

// Receive suggestions
ws.on('message', (data) => {
  const message = JSON.parse(data);
  if (message.type === 'suggestions') {
    console.log(message.suggestions);
  }
});
```

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The request body is invalid",
    "details": {
      "field": "title",
      "issue": "Required field missing"
    }
  }
}
```

### Common Error Codes

- `UNAUTHORIZED`: Invalid or missing token
- `FORBIDDEN`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `RATE_LIMITED`: Too many requests
- `INVALID_REQUEST`: Malformed request
- `SERVER_ERROR`: Internal server error

## Pagination

Paginated responses follow this format:

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 156,
    "pages": 8
  },
  "links": {
    "first": "/api/documents?page=1&limit=20",
    "prev": null,
    "next": "/api/documents?page=2&limit=20",
    "last": "/api/documents?page=8&limit=20"
  }
}
```

## Webhooks (Pro/Enterprise)

### Configure Webhook

```http
POST /api/webhooks
Content-Type: application/json

{
  "url": "https://your-server.com/webhook",
  "events": ["document.created", "citation.added"],
  "secret": "your_webhook_secret"
}
```

### Webhook Events

- `document.created`
- `document.updated`
- `document.deleted`
- `citation.added`
- `paper.processed`
- `collaboration.invited`

### Webhook Payload

```json
{
  "event": "citation.added",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "document_id": "doc_123",
    "citation": {
      "paper_id": "paper_456",
      "position": {...}
    }
  }
}
```

## SDK Support

### JavaScript/TypeScript

```bash
npm install @citation-assistant/sdk
```

```javascript
import { CitationClient } from '@citation-assistant/sdk';

const client = new CitationClient({
  apiKey: 'YOUR_API_KEY'
});

const suggestions = await client.citations.suggest({
  text: 'Your text here',
  limit: 5
});
```

### Python

```bash
pip install citation-assistant
```

```python
from citation_assistant import Client

client = Client(api_key='YOUR_API_KEY')

suggestions = client.citations.suggest(
    text='Your text here',
    limit=5
)
```

## Best Practices

1. **Cache responses** when possible
2. **Use webhooks** instead of polling
3. **Batch operations** when uploading multiple papers
4. **Handle rate limits** gracefully with exponential backoff
5. **Validate inputs** before sending requests
6. **Use compression** for large payloads
7. **Implement proper error handling**
8. **Keep tokens secure** and rotate regularly