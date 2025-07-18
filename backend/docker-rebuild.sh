#\!/bin/bash

echo "🔄 Rebuilding Docker environment for Academic Citation Assistant..."

# Stop and remove existing containers
echo "📦 Stopping existing containers..."
docker-compose down

# Remove volumes if you want a completely fresh start (optional)
# Uncomment the next line if you want to reset the database completely
# docker-compose down -v

# Rebuild images to include latest code changes
echo "🔨 Rebuilding Docker images..."
docker-compose build --no-cache

# Start the services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Run database migrations
echo "📊 Running database migrations..."
docker-compose exec backend alembic upgrade head

# Create test user
echo "👤 Creating test user..."
docker-compose exec backend python scripts/create_test_user_simple.py

# Download NLTK data
echo "📦 Downloading NLTK data..."
docker-compose exec backend python scripts/download_nltk_data.py

# Populate test data
echo "📚 Populating test papers..."
docker-compose exec backend python scripts/populate_test_papers_v2.py

echo "✅ Docker environment rebuilt successfully\!"
echo ""
echo "📍 Services available at:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "📝 To view logs: docker-compose logs -f"
echo "🛑 To stop: docker-compose down"
