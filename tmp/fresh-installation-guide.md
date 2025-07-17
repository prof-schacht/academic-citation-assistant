# Fresh Installation Guide - Academic Citation Assistant

## Quick Start for New Installations

If you're setting up the Academic Citation Assistant on a new machine and encounter database errors like "relation 'documents' does not exist", follow these steps:

### 1. Ensure Docker Containers are Running
```bash
docker-compose up -d
```

### 2. Run Database Migrations
This is the critical step that creates all necessary database tables:
```bash
docker-compose exec backend alembic upgrade head
```

### 3. (Optional) Populate Test Data
To add sample papers for testing:
```bash
docker-compose exec backend python scripts/populate_test_papers_v2.py
```

## Complete Fresh Start Process

If you want to completely reset and start fresh:

```bash
# Stop and remove everything including volumes
docker-compose down -v

# Rebuild and start
docker-compose build --no-cache
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Create test user (required for document creation)
docker-compose exec backend python scripts/create_test_user_simple.py

# Download NLTK data (required for citation recommendations)
docker-compose exec backend python scripts/download_nltk_data.py

# Populate test data
docker-compose exec backend python scripts/populate_test_papers_v2.py
```

## Using the Rebuild Script

There's also a convenient script that handles everything:
```bash
cd backend
./docker-rebuild.sh
```

This script will:
- Stop existing containers
- Rebuild Docker images
- Start services
- Run database migrations
- Populate test papers

## Verification

After setup, you can verify everything is working:

1. **Check API**: http://localhost:8000/docs
2. **Check Frontend**: http://localhost:3000
3. **Test API endpoints**:
   ```bash
   curl http://localhost:8000/api/papers/
   curl http://localhost:8000/api/documents/
   ```

## Common Issues

### "relation 'documents' does not exist" Error
This error occurs when database migrations haven't been run. Always run:
```bash
docker-compose exec backend alembic upgrade head
```

### Check Migration Status
To see current migration status:
```bash
docker-compose exec backend alembic current
```

### View Migration History
To see available migrations:
```bash
docker-compose exec backend alembic history
```