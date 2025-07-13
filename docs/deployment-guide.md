# Deployment Guide

## Overview

This guide covers deploying the Academic Citation Assistant to production environments. We'll cover multiple deployment options from simple single-server setups to scalable Kubernetes deployments.

## Deployment Options

### Option 1: Single Server (VPS)

Suitable for: Small teams, proof of concept, <1000 users

#### Requirements
- Ubuntu 22.04 LTS or similar
- 4GB RAM minimum (8GB recommended)
- 2 CPU cores
- 50GB storage
- Domain name with SSL certificate

#### Setup Steps

1. **Install Dependencies**:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install PostgreSQL and pgvector
sudo apt install -y postgresql postgresql-contrib
sudo apt install -y postgresql-14-pgvector

# Install Redis
sudo apt install -y redis-server

# Install Nginx
sudo apt install -y nginx

# Install PM2
sudo npm install -g pm2
```

2. **Configure PostgreSQL**:
```sql
sudo -u postgres psql
CREATE USER citation_user WITH PASSWORD 'secure_password';
CREATE DATABASE citation_db OWNER citation_user;
\c citation_db
CREATE EXTENSION vector;
\q
```

3. **Deploy Application**:
```bash
# Clone repository
git clone https://github.com/prof-schacht/academic-citation-assistant.git
cd academic-citation-assistant

# Install dependencies
npm install --production

# Build frontend
cd frontend
npm install
npm run build

# Build backend
cd ../backend
npm install
npm run build
```

4. **Configure Environment**:
```bash
# Create production env file
cp .env.example .env.production
# Edit with production values
```

5. **Setup PM2**:
```bash
# Start backend
pm2 start dist/server.js --name citation-api --env production

# Save PM2 configuration
pm2 save
pm2 startup
```

6. **Configure Nginx**:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/ssl/cert;
    ssl_certificate_key /path/to/ssl/key;

    # Frontend
    location / {
        root /var/www/citation-assistant/frontend/build;
        try_files $uri /index.html;
    }

    # API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
```

### Option 2: Docker Deployment

Suitable for: Medium deployments, easy scaling, <10,000 users

#### Docker Compose Production

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    restart: always
    environment:
      - REACT_APP_API_URL=https://api.your-domain.com

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    restart: always
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://user:pass@postgres:5432/citation_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  postgres:
    image: ankane/pgvector:14
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=citation_user
      - POSTGRES_PASSWORD=secure_password
      - POSTGRES_DB=citation_db

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend

volumes:
  postgres_data:
  redis_data:
```

### Option 3: Kubernetes Deployment

Suitable for: Large scale, high availability, 10,000+ users

#### Kubernetes Manifests

**1. Namespace**:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: citation-assistant
```

**2. Backend Deployment**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: citation-assistant
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: your-registry/citation-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: NODE_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

**3. Horizontal Pod Autoscaler**:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: citation-assistant
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Production Configuration

### Environment Variables

```bash
# Application
NODE_ENV=production
PORT=8000

# Database
DATABASE_URL=postgresql://user:pass@host:5432/citation_db
DATABASE_POOL_SIZE=20

# Redis
REDIS_URL=redis://host:6379
REDIS_PASSWORD=your_redis_password

# Security
JWT_SECRET=long_random_string
JWT_REFRESH_SECRET=another_long_random_string
CORS_ORIGIN=https://your-domain.com

# External APIs
SEMANTIC_SCHOLAR_API_KEY=your_api_key

# Monitoring
SENTRY_DSN=your_sentry_dsn
LOG_LEVEL=info
```

### Security Checklist

- [ ] SSL/TLS certificates configured
- [ ] Environment variables secured
- [ ] Database passwords strong
- [ ] Firewall rules configured
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] Security headers added
- [ ] Input validation active
- [ ] SQL injection prevention
- [ ] XSS protection enabled

### Performance Optimization

1. **Database**:
   - Configure connection pooling
   - Set up read replicas
   - Optimize indexes
   - Regular VACUUM

2. **Caching**:
   - Redis for session storage
   - CDN for static assets
   - Browser caching headers
   - API response caching

3. **Application**:
   - Enable gzip compression
   - Minify JavaScript/CSS
   - Optimize images
   - Lazy load components

## Monitoring & Logging

### Monitoring Stack

1. **Prometheus** for metrics
2. **Grafana** for visualization
3. **AlertManager** for alerts
4. **Sentry** for error tracking

### Key Metrics to Monitor

- API response times
- Citation suggestion accuracy
- Database query performance
- WebSocket connections
- Error rates
- User activity

### Logging Configuration

```javascript
// Winston configuration
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' }),
  ],
});

// Production logging
if (process.env.NODE_ENV === 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.simple(),
  }));
}
```

## Backup & Recovery

### Database Backup

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Backup PostgreSQL
pg_dump citation_db | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete

# Upload to S3
aws s3 cp $BACKUP_DIR/db_backup_$DATE.sql.gz s3://your-backup-bucket/
```

### Disaster Recovery Plan

1. **RTO (Recovery Time Objective)**: 4 hours
2. **RPO (Recovery Point Objective)**: 24 hours
3. **Backup locations**: Local + S3
4. **Test recovery**: Monthly

## Scaling Strategies

### Horizontal Scaling

1. **Load Balancer**: Distribute traffic
2. **Multiple API servers**: Behind LB
3. **Read replicas**: For database
4. **Redis cluster**: For caching

### Vertical Scaling

1. **Database**: Upgrade instance size
2. **Redis**: More memory
3. **API servers**: More CPU/RAM

### CDN Configuration

```javascript
// CloudFlare or AWS CloudFront
const cdnConfig = {
  origin: 'https://your-domain.com',
  cacheControl: {
    'js/': 'max-age=31536000',
    'css/': 'max-age=31536000',
    'images/': 'max-age=86400',
  },
};
```

## Maintenance

### Update Process

1. **Announce maintenance window**
2. **Backup current state**
3. **Deploy to staging**
4. **Run tests**
5. **Deploy to production**
6. **Monitor for issues**

### Zero-Downtime Deployment

```bash
# Blue-Green deployment
1. Deploy to green environment
2. Run health checks
3. Switch load balancer
4. Monitor for issues
5. Keep blue as rollback
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**:
   - Check for memory leaks
   - Increase swap space
   - Scale horizontally

2. **Slow Queries**:
   - Run EXPLAIN ANALYZE
   - Add missing indexes
   - Optimize query patterns

3. **WebSocket Disconnects**:
   - Check nginx timeout
   - Implement reconnection
   - Monitor connection pool

### Emergency Procedures

1. **Service Down**:
   ```bash
   # Quick restart
   pm2 restart all
   
   # Check logs
   pm2 logs
   
   # Rollback if needed
   ./scripts/rollback.sh
   ```

2. **Database Issues**:
   ```bash
   # Check connections
   SELECT count(*) FROM pg_stat_activity;
   
   # Kill long queries
   SELECT pg_terminate_backend(pid)
   FROM pg_stat_activity
   WHERE state = 'active' AND query_time > interval '5 minutes';
   ```

## Cost Optimization

1. **Use spot instances** for non-critical workloads
2. **Implement auto-scaling** to match demand
3. **Optimize database queries** to reduce CPU
4. **Use CDN** to reduce bandwidth costs
5. **Archive old data** to cheaper storage

This deployment guide provides comprehensive instructions for getting the Academic Citation Assistant into production, with options for different scales and requirements.