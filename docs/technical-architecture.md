# Technical Architecture

## System Overview

The Academic Citation Assistant is built as a modern web application with a microservices-inspired architecture that prioritizes scalability, performance, and user experience.

## Architecture Diagram

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Web Client    │────▶│   API Gateway    │────▶│  Backend API    │
│  (React PWA)    │     │   (Nginx)        │     │  (Node.js)      │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                           │
                        ┌──────────────────────────────────┴────────┐
                        │                                           │
                ┌───────▼────────┐                    ┌────────────▼────────┐
                │  PostgreSQL    │                    │   External APIs     │
                │  + pgvector    │                    │  (Semantic Scholar) │
                └────────────────┘                    └─────────────────────┘
```

## Core Components

### Frontend (React PWA)
- **Framework**: React 18 with TypeScript
- **Styling**: TailwindCSS for responsive design
- **Editor**: Lexical (by Meta) for rich text editing
- **State Management**: React Query for server state
- **Real-time**: WebSocket connection for live suggestions

### Backend API (Node.js)
- **Framework**: Express/Fastify
- **Language**: TypeScript
- **Authentication**: JWT with refresh tokens
- **WebSocket**: Socket.io for real-time communication
- **Queue**: Bull for background job processing

### Database Layer
- **Primary Database**: PostgreSQL 14+
- **Vector Extension**: pgvector for similarity search
- **Cache**: Redis for session and query caching
- **File Storage**: MinIO/S3 for document storage

### AI/ML Pipeline
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Vector Dimension**: 384 dimensions
- **Similarity Search**: Cosine similarity with IVFFlat index

## Data Flow

### Citation Suggestion Flow
1. User types in the editor
2. Frontend debounces input (500ms)
3. Text sent via WebSocket to backend
4. Backend generates embedding for text
5. Vector similarity search in pgvector
6. Results ranked and filtered by confidence
7. Top suggestions sent back via WebSocket
8. Frontend displays suggestions in sidebar

### Document Processing Flow
1. User uploads PDF/text file
2. Backend extracts text content
3. Text split into overlapping chunks
4. Each chunk converted to embedding
5. Embeddings stored in pgvector
6. Metadata indexed for fast retrieval

## Phase I Architecture (Local)

### Components
- Single PostgreSQL instance with pgvector
- Local embedding generation
- File-based paper storage
- In-memory caching

### Scaling Considerations
- Support up to 10,000 papers per user
- Sub-second response time for suggestions
- Efficient chunk size (500 words)

## Phase II Architecture (API Integration)

### Additional Components
- API Gateway for rate limiting
- Provider abstraction layer
- Result aggregation service
- Extended caching strategy

### External APIs
- **Semantic Scholar**: Primary academic database
- **CrossRef**: DOI resolution and metadata
- **arXiv**: Preprint papers
- **PubMed**: Biomedical literature

## Security Architecture

### Authentication & Authorization
- OAuth 2.0 with Google/GitHub
- JWT tokens with short expiry
- Refresh token rotation
- Role-based access control

### Data Security
- Encryption at rest (AES-256)
- TLS 1.3 for all connections
- CORS properly configured
- Input sanitization

## Performance Optimizations

### Frontend
- Code splitting and lazy loading
- Service worker for offline support
- Virtual scrolling for large lists
- Debounced API calls

### Backend
- Connection pooling
- Query result caching
- Batch embedding generation
- Async job processing

### Database
- IVFFlat index for vector search
- Partial indexes for common queries
- Query plan optimization
- Regular VACUUM operations

## Monitoring & Observability

### Metrics
- Response time percentiles
- Citation relevance scores
- User engagement metrics
- API usage statistics

### Logging
- Structured JSON logging
- Centralized log aggregation
- Error tracking with Sentry
- Performance monitoring

## Deployment Architecture

### Development
- Docker Compose setup
- Hot reloading
- Local SSL certificates
- Seed data scripts

### Production
- Kubernetes deployment
- Horizontal pod autoscaling
- Load balancer with health checks
- Blue-green deployments

## Technology Decisions

### Why PostgreSQL + pgvector?
- Native vector operations
- ACID compliance
- Proven scalability
- Single database solution

### Why React + PWA?
- Cross-platform compatibility
- Offline functionality
- Native-like experience
- Large ecosystem

### Why Node.js?
- JavaScript everywhere
- Excellent async handling
- Rich package ecosystem
- Fast development cycle