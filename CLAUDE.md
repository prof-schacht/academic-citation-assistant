# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Claude.md

This file provides guidance to Claude Code when working with code in this repository.

1. ALWAYS write secure best practice Python code.
2. Always try to write as lean as possible code. Don't blow up the repo. 
4 Iterate function based on test results
5. MOVE Test scripts to the tests folder if they are not already there and ensure that they could be reused for later Tests for code coverage or reruns.
6. ALWAYS commit after each new function is added to our codebase
7. Ensure that you are using uv for isolating environments and packagemanagement
8. Use tree command for project structure. If tree comand not exist install it with command: brew install tree
9. For new and open git issues which should be implemented create first a new branch and work in this branch
10. Ensure that always if a issue is completed pull requests are created.
11. Create a tmp folder for development. And create a scratchpad.md file in this folder to chronologically document the development process.
12. Give the user after each finished step a short advise how to test your implementation. 
13. Always update or create the docs/usage.md file with the newly changed functionality to know how to use the actual implementation.
14. Absolut important keep the repo lean and clean, don't add unnecessary files, don't overengineer.
15. USe Playwright for testing the frontend application. 
16. Make Screenshot of the frontend application to anlayze look and feel using Playwright.
17. Try to read the javascript console using Playwright for debugging.

## Project Overview

This is the **Academic Citation Assistant** - a real-time citation recommendation system that acts like "Grammarly for citations". It's a web application that provides intelligent, context-aware paper suggestions as researchers write their academic papers.

**Current Status**: Documentation and planning phase - no source code has been implemented yet.

## Technology Stack

- **Frontend**: React 18 + TypeScript + TailwindCSS + Lexical Editor
- **Backend**: Node.js + Express (planned)
- **Database**: PostgreSQL 14+ with pgvector extension for vector similarity search
- **Caching**: Redis
- **AI/ML**: Sentence Transformers for text embeddings (768-dimensional vectors)
- **Infrastructure**: Docker, Nginx, WebSockets for real-time features

## Planned Project Structure

```
academic-citation-assistant/
├── frontend/          # React PWA application
├── backend/           # Node.js Express API
├── shared/            # Shared TypeScript types/utilities
├── docs/             # Documentation (exists)
├── scripts/          # Build/deployment scripts
└── docker-compose.yml # Local development setup
```

## Development Commands (When Implemented)

```bash
# Setup
npm install              # Install dependencies
npm run db:migrate       # Run database migrations
npm run db:seed          # Seed sample data

# Development
npm run dev              # Start development servers
npm test                 # Run unit tests
npm run test:coverage    # Run tests with coverage
npm run test:integration # Run integration tests
npm run test:e2e         # Run end-to-end tests

# Code Quality
npm run lint             # ESLint checking
npm run format           # Prettier formatting
npm run typecheck        # TypeScript type checking

# Production
npm run build            # Production build
npm run analyze          # Bundle analysis
```

## Architecture Notes

### Core Features
- **Real-time Citation Engine**: Uses WebSocket connections for live suggestions as users type
- **Vector Search**: Implements semantic similarity using pgvector with cosine distance
- **Multi-source Integration**: Combines local paper libraries with external APIs (Semantic Scholar, PubMed, arXiv)
- **Progressive Web App**: Full offline capabilities and mobile responsiveness

### Data Flow
1. User types in Lexical Editor
2. Text is converted to 768-dimensional embeddings using Sentence Transformers
3. Vector similarity search against PostgreSQL with pgvector
4. Results ranked by confidence scores and displayed in real-time
5. Citation insertion updates document state and exports to various formats

### Database Schema (Planned)
- **users**: Authentication and preferences
- **documents**: User's papers and collaborations  
- **papers**: Academic paper metadata and vectors
- **citations**: Relationship between documents and papers
- **libraries**: User's personal paper collections

## Environment Setup Requirements

### Required Software
- Node.js 18+
- PostgreSQL 14+ with pgvector extension
- Redis 6+
- Docker 20+ (optional)

### Environment Variables
- Database connection strings
- Redis URLs
- JWT secrets for authentication
- External API keys (Semantic Scholar, etc.)
- Storage configuration (local/S3)

## Development Workflow

### Git Conventions
- Feature branches: `feature/description`
- Commit format: `type: description` (feat:, fix:, docs:, etc.)
- All commits must pass linting and type checking

### Code Style
- TypeScript strict mode enabled
- ESLint with Airbnb configuration
- Prettier with 2-space indentation
- 80% test coverage minimum

## Key Technical Considerations

### Performance
- Implement query optimization for vector searches
- Use Redis caching for frequently accessed papers
- Code splitting for React components
- Virtual scrolling for large result sets

### Security
- JWT-based authentication with refresh tokens
- Input sanitization for all text processing
- Rate limiting on API endpoints
- Secure file upload handling

### Scalability
- Horizontal scaling via Docker containers
- Database read replicas for search operations
- CDN integration for static assets
- Background job queues for heavy processing

## External Dependencies (When Implemented)

The project will integrate with external academic APIs:
- **Semantic Scholar**: Primary source for academic papers
- **PubMed**: Medical and life science papers
- **arXiv**: Preprints and research papers
- **CrossRef**: DOI resolution and metadata

Rate limiting and error handling must be implemented for all external API calls.

## Current Documentation

Comprehensive documentation exists in `/docs/`:
- `technical-architecture.md`: Detailed system design
- `development-guide.md`: Setup and workflow instructions  
- `api-documentation.md`: Planned API reference
- `user-guide.md`: End-user documentation
- `deployment-guide.md`: Production deployment guide

Refer to these documents for detailed specifications when implementing features.