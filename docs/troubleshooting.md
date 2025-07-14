# Troubleshooting Guide

## Common Issues and Solutions

### Frontend Dependencies Not Found in Docker

**Problem**: After adding new npm packages, you get errors like:
```
Failed to resolve import "package-name" from "src/..."
```

**Solution**: The frontend Docker container needs to be rebuilt to install new dependencies:

```bash
# Option 1: Rebuild just the frontend
docker-compose stop frontend
docker-compose build frontend
docker-compose up -d frontend

# Option 2: If that doesn't work, force a complete rebuild
docker-compose build --no-cache frontend
docker-compose up -d frontend

# Option 3: Install manually in running container (temporary fix)
docker-compose exec frontend npm install
```

### WebSocket Connection Issues

**Problem**: Citation suggestions show "Not connected" despite WebSocket connecting.

**Solution**: 
1. Check backend logs: `docker-compose logs backend -f`
2. Ensure test papers are loaded: `docker-compose exec backend python scripts/populate_test_papers_v2.py`
3. Refresh the browser page (Cmd+R or F5)

### Paper Upload Processing Errors

**Problem**: Papers stuck in "Processing" state or show errors.

**Solution**:
1. Check backend logs for specific errors
2. Ensure MarkItDown dependencies are installed: `docker-compose exec backend uv sync`
3. Try reprocessing: Click the retry button in Paper Library

### Database Connection Errors

**Problem**: "Failed to connect to database" errors.

**Solution**:
1. Ensure PostgreSQL is running: `docker-compose ps`
2. Check if migrations ran: `docker-compose exec backend alembic upgrade head`
3. Reset database if needed: `docker-compose down -v` (WARNING: Deletes all data)

### Import Errors in Frontend

**Problem**: TypeScript errors like "Importing binding name 'X' is not found"

**Solution**: These usually indicate incorrect import syntax:
- For types: Use `import type { TypeName } from 'module'`
- For interfaces: Ensure they're imported as types, not values
- Check that named exports match: `export { Component }` needs `import { Component }`

### Docker Build Failures

**Problem**: Docker build fails with network errors or timeouts.

**Solution**:
1. Clean Docker cache: `docker system prune -a` (WARNING: Removes all unused images)
2. Update Docker Desktop to latest version
3. Check disk space: `docker system df`
4. Try building with limited parallelism: `docker-compose build --parallel 1`

### Performance Issues

**Problem**: Application runs slowly or freezes.

**Solution**:
1. Allocate more resources to Docker Desktop (Preferences > Resources)
2. Reduce number of papers being processed simultaneously
3. Check CPU/Memory usage: `docker stats`
4. Restart services: `docker-compose restart`

## Getting Help

If you encounter issues not covered here:

1. Check the logs:
   - Backend: `docker-compose logs backend -f`
   - Frontend: `docker-compose logs frontend -f`
   - Database: `docker-compose logs postgres -f`

2. Search existing GitHub issues: https://github.com/prof-schacht/academic-citation-assistant/issues

3. Create a new issue with:
   - Description of the problem
   - Steps to reproduce
   - Error messages from logs
   - Your environment (OS, Docker version, etc.)