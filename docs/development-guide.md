# Development Guide

## Prerequisites

### Required Software

- **Node.js**: 18.x or higher
- **PostgreSQL**: 14+ with pgvector extension
- **Redis**: 6.x or higher
- **Docker**: 20.x or higher (optional)
- **Git**: 2.x or higher

### Recommended Tools

- **VS Code** with extensions:
  - ESLint
  - Prettier
  - TypeScript
  - Tailwind CSS IntelliSense
- **PostgreSQL client**: pgAdmin or TablePlus
- **Redis client**: RedisInsight
- **API testing**: Postman or Insomnia

## Project Structure

```
academic-citation-assistant/
├── frontend/                 # React application
│   ├── src/
│   │   ├── components/      # Reusable components
│   │   ├── pages/          # Page components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── services/       # API services
│   │   ├── utils/          # Utility functions
│   │   └── types/          # TypeScript types
│   ├── public/             # Static assets
│   └── package.json
├── backend/                 # Node.js API
│   ├── src/
│   │   ├── controllers/    # Route controllers
│   │   ├── services/       # Business logic
│   │   ├── models/         # Database models
│   │   ├── middleware/     # Express middleware
│   │   ├── utils/          # Utilities
│   │   └── types/          # TypeScript types
│   ├── migrations/         # Database migrations
│   └── package.json
├── shared/                  # Shared types/utilities
├── docs/                    # Documentation
├── scripts/                 # Build/deploy scripts
└── docker-compose.yml       # Local development
```

## Setting Up Development Environment

### 1. Clone the Repository

```bash
git clone https://github.com/prof-schacht/academic-citation-assistant.git
cd academic-citation-assistant
```

### 2. Install Dependencies

```bash
# Install root dependencies
npm install

# Install frontend dependencies
cd frontend
npm install

# Install backend dependencies
cd ../backend
npm install
```

### 3. Set Up Environment Variables

```bash
# Backend environment
cp backend/.env.example backend/.env

# Frontend environment
cp frontend/.env.example frontend/.env
```

Edit the `.env` files with your configuration:

**Backend `.env`**:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/citation_db

# Redis
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET=your_jwt_secret_here
JWT_REFRESH_SECRET=your_refresh_secret_here

# External APIs (Phase II)
SEMANTIC_SCHOLAR_API_KEY=your_api_key

# Storage
STORAGE_TYPE=local
STORAGE_PATH=./uploads
```

**Frontend `.env`**:
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

### 4. Set Up Database

```bash
# Create database
createdb citation_db

# Install pgvector extension
psql citation_db -c "CREATE EXTENSION vector;"

# Run migrations
cd backend
npm run db:migrate

# Seed sample data (optional)
npm run db:seed
```

### 5. Start Development Servers

```bash
# Start all services with Docker
docker-compose up

# OR start services individually:

# Terminal 1: Backend
cd backend
npm run dev

# Terminal 2: Frontend
cd frontend
npm start

# Terminal 3: Redis (if not using Docker)
redis-server
```

## Development Workflow

### Git Workflow

1. **Create feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and commit**:
   ```bash
   git add .
   git commit -m "feat: add citation filtering"
   ```

3. **Push and create PR**:
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Convention

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test updates
- `chore:` Build/tooling changes

### Code Style

- **TypeScript**: Strict mode enabled
- **Linting**: ESLint with Airbnb config
- **Formatting**: Prettier with 2-space indent
- **Import order**: External, internal, relative

## Testing

### Unit Tests

```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Watch mode
npm run test:watch
```

### Integration Tests

```bash
# Backend API tests
cd backend
npm run test:integration

# Frontend E2E tests
cd frontend
npm run test:e2e
```

### Testing Guidelines

1. **Test file naming**: `*.test.ts` or `*.spec.ts`
2. **Test structure**: Arrange-Act-Assert
3. **Coverage target**: 80% minimum
4. **Mock external services**

## Building Features

### Adding a New API Endpoint

1. **Define route** in `backend/src/routes/`
2. **Create controller** in `backend/src/controllers/`
3. **Implement service** in `backend/src/services/`
4. **Add validation** using Joi or Zod
5. **Write tests**
6. **Update API documentation**

### Adding a Frontend Component

1. **Create component** in `frontend/src/components/`
2. **Define TypeScript types**
3. **Style with Tailwind**
4. **Add to Storybook** (optional)
5. **Write unit tests**
6. **Update component documentation**

### Database Migrations

```bash
# Create new migration
npm run db:migration:create add_user_preferences

# Run migrations
npm run db:migrate

# Rollback
npm run db:rollback
```

## Performance Optimization

### Frontend

1. **Code splitting**: Use React.lazy for routes
2. **Memoization**: Use React.memo and useMemo
3. **Virtual scrolling**: For long lists
4. **Image optimization**: Use WebP format
5. **Bundle analysis**: `npm run analyze`

### Backend

1. **Query optimization**: Use EXPLAIN ANALYZE
2. **Caching strategy**: Redis for hot data
3. **Connection pooling**: Configure pool size
4. **Async operations**: Use queues for heavy tasks
5. **Monitoring**: APM tools integration

## Debugging

### Frontend Debugging

1. **React DevTools**: Component inspection
2. **Redux DevTools**: State debugging
3. **Network tab**: API call analysis
4. **Console logs**: Structured logging

### Backend Debugging

1. **VS Code debugger**: Breakpoint debugging
2. **Logger**: Winston with log levels
3. **Database queries**: Query logging
4. **Performance**: Node.js profiler

## Common Issues

### pgvector Installation

```bash
# macOS
brew install pgvector

# Ubuntu/Debian
sudo apt install postgresql-14-pgvector

# From source
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

### Port Conflicts

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Database Connection Issues

1. Check PostgreSQL is running
2. Verify connection string
3. Check firewall settings
4. Review pg_hba.conf

## Deployment Preparation

### Production Build

```bash
# Frontend
cd frontend
npm run build

# Backend
cd backend
npm run build
```

### Environment Variables

- Never commit `.env` files
- Use environment-specific configs
- Validate all required vars on startup
- Document all variables

### Health Checks

Implement health check endpoints:
- `/health`: Basic health
- `/health/ready`: Readiness probe
- `/health/live`: Liveness probe

## Resources

### Documentation

- [React Documentation](https://react.dev)
- [TypeScript Handbook](https://www.typescriptlang.org/docs)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Tailwind CSS](https://tailwindcss.com/docs)

### Learning Resources

- Project architecture decisions
- Code review guidelines
- Performance best practices
- Security considerations

### Getting Help

- GitHub Issues for bugs
- Discussions for questions
- Discord community (coming soon)
- Stack Overflow tag: `citation-assistant`