#!/bin/bash

# BenchHub Plus Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-production}
PROJECT_NAME="benchhub-plus"

echo -e "${BLUE}🚀 Starting BenchHub Plus deployment (${ENVIRONMENT})${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Create necessary directories
echo -e "${YELLOW}📁 Creating directories...${NC}"
mkdir -p logs
mkdir -p ssl
mkdir -p data/postgres
mkdir -p data/redis

# Set permissions
chmod 755 logs
chmod 755 ssl

# Check environment file
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${RED}❗ Please edit .env file with your configuration before continuing.${NC}"
    exit 1
fi

# Load environment variables
source .env

# Validate required environment variables
required_vars=("OPENAI_API_KEY" "POSTGRES_PASSWORD")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}❌ Required environment variable $var is not set.${NC}"
        exit 1
    fi
done

# Choose docker-compose file based on environment
if [ "$ENVIRONMENT" = "development" ]; then
    COMPOSE_FILE="docker-compose.dev.yml"
    echo -e "${YELLOW}🔧 Using development configuration${NC}"
else
    COMPOSE_FILE="docker-compose.yml"
    echo -e "${GREEN}🏭 Using production configuration${NC}"
fi

# Stop existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose -f $COMPOSE_FILE down --remove-orphans

# Pull latest images
echo -e "${YELLOW}📥 Pulling latest images...${NC}"
docker-compose -f $COMPOSE_FILE pull

# Build custom images
echo -e "${YELLOW}🔨 Building custom images...${NC}"
docker-compose -f $COMPOSE_FILE build --no-cache

# Start services
echo -e "${YELLOW}🚀 Starting services...${NC}"
docker-compose -f $COMPOSE_FILE up -d

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 30

# Check service health
echo -e "${YELLOW}🏥 Checking service health...${NC}"

# Check PostgreSQL
if docker-compose -f $COMPOSE_FILE exec -T postgres pg_isready -U benchhub > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
else
    echo -e "${RED}❌ PostgreSQL is not ready${NC}"
fi

# Check Redis
if docker-compose -f $COMPOSE_FILE exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is ready${NC}"
else
    echo -e "${RED}❌ Redis is not ready${NC}"
fi

# Check Backend API
if curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend API is ready${NC}"
else
    echo -e "${RED}❌ Backend API is not ready${NC}"
fi

# Check Frontend
if curl -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend is ready${NC}"
else
    echo -e "${RED}❌ Frontend is not ready${NC}"
fi

# Run database migrations
echo -e "${YELLOW}🗄️  Running database migrations...${NC}"
docker-compose -f $COMPOSE_FILE exec backend python -c "
from apps.core.db import init_db
init_db()
print('Database initialized successfully')
"

# Show service URLs
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${BLUE}📋 Service URLs:${NC}"

if [ "$ENVIRONMENT" = "development" ]; then
    echo -e "  • Frontend: ${GREEN}http://localhost:8502${NC}"
    echo -e "  • Backend API: ${GREEN}http://localhost:8001${NC}"
    echo -e "  • API Docs: ${GREEN}http://localhost:8001/docs${NC}"
    echo -e "  • Flower (Celery): ${GREEN}http://localhost:5556${NC}"
    echo -e "  • PostgreSQL: ${GREEN}localhost:5433${NC}"
    echo -e "  • Redis: ${GREEN}localhost:6380${NC}"
else
    echo -e "  • Frontend: ${GREEN}http://localhost:8501${NC}"
    echo -e "  • Backend API: ${GREEN}http://localhost:8000${NC}"
    echo -e "  • API Docs: ${GREEN}http://localhost:8000/docs${NC}"
    echo -e "  • Flower (Celery): ${GREEN}http://localhost:5555${NC}"
    echo -e "  • Nginx Proxy: ${GREEN}http://localhost${NC}"
fi

# Show logs command
echo -e "${BLUE}📊 To view logs:${NC}"
echo -e "  docker-compose -f $COMPOSE_FILE logs -f [service_name]"

# Show status command
echo -e "${BLUE}📈 To check status:${NC}"
echo -e "  docker-compose -f $COMPOSE_FILE ps"

echo -e "${GREEN}✨ BenchHub Plus is now running!${NC}"