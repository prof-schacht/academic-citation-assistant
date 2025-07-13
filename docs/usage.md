# Usage Guide - Academic Citation Assistant

## Current Implementation Status (Phase I - In Progress)

### What's Working Now

1. **Backend API**:
   - FastAPI server with health check endpoints
   - `/api/health` - Basic health check
   - `/api/health/ready` - Readiness probe (checks Redis)
   - `/api/health/live` - Liveness probe

2. **Frontend**:
   - React app with TypeScript and TailwindCSS
   - Basic landing page with project information
   - Responsive design

3. **Infrastructure**:
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

### Coming Soon
- Document management endpoints
- Citation suggestion endpoints
- Paper upload and processing
- User authentication

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

- Database models and migrations
- Paper upload functionality
- Text extraction from PDFs
- Vector embeddings generation
- Real-time citation suggestions
- Document editor with Lexical

---

Last updated: 2025-07-13