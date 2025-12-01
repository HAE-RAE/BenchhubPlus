# Docker Deployment Guide

Complete guide for deploying BenchHub Plus using Docker and Docker Compose.

## 🐳 Overview

BenchHub Plus uses a multi-container Docker architecture with the following services:

- **Frontend**: Streamlit web interface
- **Backend**: FastAPI REST API
- **Worker**: Celery task processor
- **Database**: PostgreSQL data storage
- **Cache**: Redis for caching and task queue
- **Proxy**: Nginx reverse proxy (production)

## 📋 Prerequisites

### System Requirements

- **Docker**: 20.10+ 
- **Docker Compose**: 2.0+
- **Memory**: 4GB+ RAM
- **Storage**: 10GB+ free space
- **Network**: Internet connection for model APIs

### Installation

**Ubuntu/Debian:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

**macOS:**
```bash
# Install Docker Desktop
brew install --cask docker
```

**Windows:**
Install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)

## 🚀 Quick Deployment

### Development Deployment

```bash
# Clone repository
git clone https://github.com/HAE-RAE/BenchhubPlus.git
cd BenchhubPlus

# Setup environment
./scripts/setup.sh

# Configure environment variables
cp .env.example .env
# Edit .env with your settings

# Prepare seed data (IMPORTANT)
# Ensure seeds/seed_data.parquet exists before deployment
# See "Database Seeding" section below for details

# Deploy development environment
./scripts/deploy.sh development
```

**Access Points:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

### Production Deployment

```bash
# Deploy production environment
./scripts/deploy.sh production
```

**Access Points:**
- Application: http://localhost (port 80 via Nginx) or http://localhost:3000
- API: http://localhost/api or http://localhost:8000/api
- Health Check: http://localhost/api/v1/health

## 🔧 Configuration

### Environment Variables

Create and configure `.env` file:

```env
# Required Settings
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=generate_a_minimum_32_byte_secret
CORS_ALLOWED_ORIGINS=https://your-frontend.example.com
POSTGRES_PASSWORD=secure_database_password

# Optional Settings
DEBUG=false
LOG_LEVEL=info
POSTGRES_USER=benchhub
POSTGRES_DB=benchhub_plus
REDIS_URL=redis://redis:6379/0

# Production Settings
DOMAIN=your-domain.com
SSL_EMAIL=your-email@domain.com
```

### Secret Rotation

BenchHub Plus never ships with default secrets. Rotate credentials routinely:

1. **Generate new secrets**: create a fresh `SECRET_KEY` and replace any external API keys in a secure secret manager.
2. **Update environment**: deploy the new values to the runtime environment (Kubernetes secret, Docker Compose `.env`, etc.).
3. **Restart services**: restart the backend, workers, and any scheduled jobs so they load the updated secrets. Workers use encrypted credentials and will pick up the new keys immediately after restart.
4. **Verify**: call `GET /api/v1/health` to ensure the backend reports `healthy` and Celery workers respond with the new configuration.

### Docker Compose Files

#### Development (`docker-compose.dev.yml`)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-benchhub_plus}
      POSTGRES_USER: ${POSTGRES_USER:-benchhub}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-benchhub}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER:-benchhub}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-benchhub_plus}
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEBUG=${DEBUG:-true}
      - LOG_LEVEL=${LOG_LEVEL:-debug}
    ports:
      - "8001:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER:-benchhub}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-benchhub_plus}
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LOG_LEVEL=${LOG_LEVEL:-debug}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      backend:
        condition: service_started
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  reflex:
    build:
      context: .
      dockerfile: Dockerfile.reflex
    environment:
      - API_BASE_URL=http://backend:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend
    volumes:
      - ./apps/reflex_frontend:/app
    command: ["reflex", "run", "--env", "dev", "--backend-host", "0.0.0.0", "--backend-port", "8001", "--frontend-host", "0.0.0.0", "--frontend-port", "3000", "--loglevel", "debug"]
    restart: unless-stopped

volumes:
  postgres_data:
```

#### Production (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - reflex
      - backend
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-benchhub_plus}
      POSTGRES_USER: ${POSTGRES_USER:-benchhub}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-benchhub}"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER:-benchhub}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-benchhub_plus}
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEBUG=false
      - LOG_LEVEL=info
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    deploy:
      replicas: 2

  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER:-benchhub}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-benchhub_plus}
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LOG_LEVEL=info
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    deploy:
      replicas: 3

  reflex:
    build:
      context: .
      dockerfile: Dockerfile.reflex
    environment:
      - API_BASE_URL=http://backend:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

## 🏗️ Custom Dockerfiles

### Backend Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml .
RUN pip install -e .

# Copy application code
COPY apps/ apps/
COPY scripts/ scripts/

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run application
CMD ["uvicorn", "apps.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Worker Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml .
RUN pip install -e .

# Copy application code
COPY apps/ apps/
COPY scripts/ scripts/

# Create logs directory
RUN mkdir -p logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD celery -A apps.worker.celery_app inspect ping || exit 1

# Run worker
CMD ["celery", "-A", "apps.worker.celery_app", "worker", "--loglevel=info"]
```

### Frontend Dockerfile (Reflex)

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY apps/reflex_frontend/requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY apps/reflex_frontend/ ./

# Install Node.js dependencies and build frontend
RUN reflex init --loglevel debug
RUN reflex export --frontend-only --no-zip

# Expose ports
EXPOSE 3000 8001

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Run Reflex
CMD ["reflex", "run", "--env", "prod", "--backend-host", "0.0.0.0", "--backend-port", "8001", "--frontend-host", "0.0.0.0", "--frontend-port", "3000"]
```

## 🔄 Deployment Scripts

### Setup Script (`scripts/setup.sh`)

```bash
#!/bin/bash

echo "🚀 Setting up BenchHub Plus..."

# Create necessary directories
mkdir -p logs
mkdir -p data/postgres
mkdir -p data/redis

# Copy environment template if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📝 Created .env file. Please edit it with your settings."
fi

# Make scripts executable
chmod +x scripts/*.sh

# Pull required Docker images
docker-compose -f docker-compose.dev.yml pull

echo "✅ Setup complete!"
echo "📝 Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run: ./scripts/deploy.sh development"
```

### Deployment Script (`scripts/deploy.sh`)

```bash
#!/bin/bash

ENVIRONMENT=${1:-development}

echo "🚀 Deploying BenchHub Plus ($ENVIRONMENT)..."

if [ "$ENVIRONMENT" = "production" ]; then
    COMPOSE_FILE="docker-compose.yml"
    echo "🏭 Production deployment"
else
    COMPOSE_FILE="docker-compose.dev.yml"
    echo "🔧 Development deployment"
fi

# Stop existing containers
docker-compose -f $COMPOSE_FILE down

# Build and start services
docker-compose -f $COMPOSE_FILE up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Run health checks
echo "🏥 Running health checks..."
./scripts/health-check.sh

echo "✅ Deployment complete!"

if [ "$ENVIRONMENT" = "development" ]; then
    echo "🌐 Access points:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend:  http://localhost:8001"
    echo "  API Docs: http://localhost:8001/docs"
else
    echo "🌐 Access points:"
    echo "  Application: http://localhost"
    echo "  API: http://localhost/api"
fi
```

## 📊 Monitoring and Logging

### Log Management

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f worker
docker-compose logs -f reflex

# View recent logs
docker-compose logs --tail=100 backend
```

### Health Monitoring

```bash
# Check service status
docker-compose ps

# Check health status
curl http://localhost:8001/api/v1/health

# Monitor resource usage
docker stats
```

### Log Rotation

Configure log rotation in production:

```bash
# /etc/logrotate.d/benchhub
/path/to/BenchhubPlus/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        docker-compose restart backend worker
    endscript
}
```

## 🔧 Maintenance

### Backup and Restore

**Database Backup:**
```bash
# Create backup
docker-compose exec postgres pg_dump -U benchhub benchhub_plus > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U benchhub benchhub_plus < backup.sql
```

**Volume Backup:**
```bash
# Backup volumes
docker run --rm -v benchhub_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
```

### Updates

```bash
# Pull latest images
docker-compose pull

# Rebuild and restart
docker-compose up -d --build

# Clean up old images
docker image prune -f
```

### Scaling

**Scale Workers:**
```bash
# Scale to 5 workers
docker-compose up -d --scale worker=5

# Scale backend instances
docker-compose up -d --scale backend=3
```

## 🚨 Troubleshooting

### Common Issues

**Port Conflicts:**
```bash
# Check port usage
sudo lsof -i :8001
sudo lsof -i :3000
sudo lsof -i :8000

# Kill conflicting processes
sudo kill -9 <PID>
```

**Database Connection Issues:**
```bash
# Check database logs
docker-compose logs postgres

# Test database connection
docker-compose exec postgres psql -U benchhub -d benchhub_plus -c "SELECT 1;"
```

**Memory Issues:**
```bash
# Check memory usage
docker stats

# Increase Docker memory limit
# Docker Desktop: Settings > Resources > Memory
```

### Recovery Procedures

**Complete Reset:**
```bash
# Stop all services
docker-compose down -v

# Remove all data
docker volume prune -f

# Redeploy
./scripts/deploy.sh development
```

**Service Recovery:**
```bash
# Restart specific service
docker-compose restart backend

# Rebuild specific service
docker-compose up -d --build backend
```

## 🔐 Security Considerations

### Production Security

1. **Use secrets management**:
   ```bash
   # Use Docker secrets
   echo "your_secret" | docker secret create openai_key -
   ```

2. **Enable SSL/TLS**:
   - Configure SSL certificates
   - Use HTTPS only
   - Enable HSTS headers

3. **Network security**:
   - Use custom networks
   - Limit exposed ports
   - Enable firewall rules

4. **Regular updates**:
   - Update base images
   - Apply security patches
   - Monitor vulnerabilities

### Environment Isolation

```yaml
# Custom network
networks:
  benchhub_network:
    driver: bridge

services:
  backend:
    networks:
      - benchhub_network
    # Remove port exposure in production
```

## 🗄️ Database Seeding

BenchHub Plus uses an automated Parquet-based database seeding system that initializes the leaderboard with pre-aggregated benchmark data.

### Seed Data Requirements

**Critical**: Before deploying, ensure the `seeds/seed_data.parquet` file exists in your repository root. This file contains pre-aggregated evaluation results and is automatically loaded during container startup.

#### Seed File Schema

The Parquet file must contain the following columns:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `model_name` | string | Unique model identifier | "Qwen_Qwen2.5-72B-Instruct" |
| `language` | string | Evaluation language | "Korean", "English" |
| `subject_type` | string | Subject category | "HASS/Economics", "Tech./Coding" |
| `task_type` | string | Task type | "Knowledge", "Reasoning" |
| `score` | float64 | Performance score (0.0-1.0) | 0.852 |

#### Docker Integration

The `Dockerfile.backend` automatically copies the seed file into the container:

```dockerfile
# Create data directory
RUN mkdir -p /app/data

# Copy seed data file
COPY seeds/seed_data.parquet /app/data/seed_data.parquet
```

#### Seeding Process

1. **Startup Check**: When the backend container starts, it checks if the LeaderboardCache table is empty
2. **Automatic Seeding**: If empty, it reads `seeds/seed_data.parquet` and populates the database
3. **Idempotent Operation**: If data already exists, seeding is skipped to prevent duplicates
4. **Logging**: All seeding operations are logged for monitoring

#### Expected Log Messages

**First deployment (empty database):**
```
INFO:apps.backend.seeding:Database is empty. Seeding initial data from 'data/seed_data.parquet'...
INFO:apps.backend.seeding:Preparing to seed 4528 score records into LeaderboardCache...
INFO:apps.backend.seeding:Database seeding complete. Added 4528 records.
```

**Subsequent deployments (existing data):**
```
INFO:apps.backend.seeding:LeaderboardCache already contains data. Skipping seeding.
```

#### Missing Seed File

If the seed file is missing, the application will start normally but with an empty leaderboard:

```
WARNING:apps.backend.seeding:Seed file not found at 'data/seed_data.parquet'. Skipping.
```

#### Generating Seed Data

To create your own seed data file:

```python
import pandas as pd

# Aggregate your evaluation results
data = []
for result in your_evaluation_results:
    data.append({
        'model_name': result['model'],
        'language': result['language'],
        'subject_type': result['subject'],
        'task_type': result['task'],
        'score': result['aggregated_score']
    })

# Create Parquet file
df = pd.DataFrame(data)
df.to_parquet('seeds/seed_data.parquet', index=False)
print(f"Created seed file with {len(df)} records")
```

### Troubleshooting Seeding Issues

**Problem**: Container fails to start with seeding errors
**Solution**: Check that `seeds/seed_data.parquet` exists and has the correct schema

**Problem**: Duplicate data after restart
**Solution**: This shouldn't happen due to idempotency checks. If it does, check the LeaderboardRepository.get_leaderboard() method

**Problem**: Seeding takes too long
**Solution**: Consider optimizing the seed file size or implementing bulk insert operations

---

*For additional deployment questions or issues, please check our [Troubleshooting Guide](troubleshooting.md) or open an issue on GitHub.*
