# Docker Commands for Academic Citation Assistant

## Quick Rebuild and Restart

### Option 1: Full Rebuild (Recommended after code changes)
```bash
# Stop everything and rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Option 2: Quick Restart (for minor changes)
```bash
# Just restart containers
docker-compose restart

# Or restart specific service
docker-compose restart frontend
docker-compose restart backend
```

### Option 3: Complete Fresh Start (Reset database)
```bash
# Stop and remove everything including volumes
docker-compose down -v

# Rebuild and start
docker-compose build --no-cache
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Populate test data
docker-compose exec backend python scripts/populate_test_papers_v2.py
```

## Common Docker Commands

### Start services
```bash
docker-compose up -d
```

### Stop services
```bash
docker-compose down
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Execute commands in containers
```bash
# Run Python scripts in backend
docker-compose exec backend python scripts/populate_test_papers_v2.py

# Access backend shell
docker-compose exec backend bash

# Access database
docker-compose exec postgres psql -U citation_user -d citation_db
```

### Check service status
```bash
docker-compose ps
```

## Troubleshooting

### If frontend shows import errors after rebuild:
```bash
# Force rebuild frontend with clean node_modules
docker-compose stop frontend
docker-compose build frontend --no-cache
docker-compose up -d frontend
```

### If backend fails to connect to database:
```bash
# Ensure database is ready
docker-compose exec postgres pg_isready -U citation_user -d citation_db

# Check database logs
docker-compose logs postgres
```

### If changes aren't reflected:
1. Make sure volumes are mounted correctly in docker-compose.yml
2. For frontend changes, the dev server should hot-reload
3. For backend changes, the server should auto-restart
4. If not, manually restart the affected service:
   ```bash
   docker-compose restart backend
   # or
   docker-compose restart frontend
   ```

## Access Points
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Database: localhost:5432
- Redis: localhost:6379