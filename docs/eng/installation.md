# Installation Guide

This guide covers different installation methods for BenchHub Plus.

## 📋 Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows with WSL2
- **Python**: 3.11 or higher
- **Memory**: Minimum 4GB RAM (8GB+ recommended)
- **Storage**: 2GB free space
- **Network**: Internet connection for API calls

### Required Services
- **PostgreSQL**: 12+ (or use Docker)
- **Redis**: 6+ (or use Docker)

### API Keys
- **OpenAI API Key**: Required for planner agent
- **Model API Keys**: For the models you want to evaluate

## 🚀 Quick Installation (Docker - Recommended)

The fastest way to get started is using Docker:

```bash
# Clone the repository
git clone https://github.com/HAE-RAE/BenchhubPlus.git
cd BenchhubPlus

# Setup environment
./scripts/setup.sh

# Edit configuration
cp .env.example .env
# Edit .env with your API keys

# Deploy with Docker
./scripts/deploy.sh development
```

Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

## 🐳 Docker Installation (Detailed)

### 1. Install Docker and Docker Compose

**Ubuntu/Debian:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**macOS:**
```bash
# Install Docker Desktop
brew install --cask docker
```

**Windows:**
Install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)

### 2. Clone and Setup

```bash
git clone https://github.com/HAE-RAE/BenchhubPlus.git
cd BenchhubPlus

# Make scripts executable
chmod +x scripts/*.sh

# Run setup
./scripts/setup.sh
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your settings
nano .env
```

Required environment variables:
```env
# API Keys
OPENAI_API_KEY=your_openai_api_key_here

# Database
POSTGRES_PASSWORD=secure_password_here

# Optional: Custom settings
DEBUG=false
LOG_LEVEL=info
```

### 4. Deploy

```bash
# Development deployment
./scripts/deploy.sh development

# Production deployment
./scripts/deploy.sh production
```

## 🔧 Local Development Installation

For development without Docker:

### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
sudo apt install -y postgresql postgresql-contrib redis-server
sudo apt install -y build-essential libpq-dev
```

**macOS:**
```bash
brew install python@3.11 postgresql redis
```

### 2. Setup Python Environment

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -e .
```

### 3. Setup Database

**PostgreSQL:**
```bash
# Start PostgreSQL
sudo systemctl start postgresql  # Linux
brew services start postgresql   # macOS

# Create database and user
sudo -u postgres psql
```

```sql
CREATE DATABASE benchhub_plus;
CREATE USER benchhub WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE benchhub_plus TO benchhub;
\q
```

**Redis:**
```bash
# Start Redis
sudo systemctl start redis  # Linux
brew services start redis   # macOS
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with local database settings:
```env
DATABASE_URL=postgresql://benchhub:your_password@localhost:5432/benchhub_plus
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
OPENAI_API_KEY=your_openai_api_key_here
```

### 5. Initialize Database

```bash
python -c "from apps.core.db import init_db; init_db()"
```

### 6. Start Services

```bash
# Terminal 1: Backend API
./scripts/dev-backend.sh

# Terminal 2: Celery Worker
./scripts/dev-worker.sh

# Terminal 3: Frontend
./scripts/dev-frontend.sh
```

## 🔍 Verification

After installation, verify everything is working:

### 1. Check Service Health

```bash
# API Health Check
curl http://localhost:8001/api/v1/health   # use 8000 for production compose

# Expected response:
# {"status": "healthy", "database_status": "connected", "redis_status": "connected"}
```

### 2. Access Web Interface

Open http://localhost:3000 and verify:
- ✅ Page loads without errors
- ✅ Can navigate between tabs
- ✅ System status shows all services healthy

### 3. Test Basic Functionality

1. Go to "Evaluate" tab
2. Enter a simple query: "Test basic functionality"
3. Configure a test model (you can use dummy values for testing)
4. Submit evaluation
5. Check "Status" tab for task progress

## 🚨 Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Check what's using the port
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>
```

**Database Connection Failed:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -h localhost -U benchhub -d benchhub_plus
```

**Redis Connection Failed:**
```bash
# Check Redis status
sudo systemctl status redis

# Test connection
redis-cli ping
```

**Docker Issues:**
```bash
# Check Docker status
docker --version
docker-compose --version

# View logs
docker-compose logs -f [service_name]

# Reset everything
docker-compose down -v
docker system prune -a
```

### Getting Help

If you encounter issues:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Search [existing issues](https://github.com/HAE-RAE/BenchhubPlus/issues)
3. Create a new issue with:
   - Your operating system
   - Installation method used
   - Complete error messages
   - Steps to reproduce

## 🔄 Updating

### Docker Installation
```bash
git pull origin main
./scripts/deploy.sh [environment]
```

### Local Installation
```bash
git pull origin main
source venv/bin/activate
pip install -e .
# Restart services
```

## 🗑️ Uninstallation

### Docker
```bash
# Stop and remove containers
docker-compose down -v

# Remove images
docker rmi $(docker images "benchhub*" -q)

# Remove project directory
cd ..
rm -rf BenchhubPlus
```

### Local
```bash
# Deactivate virtual environment
deactivate

# Remove project directory
cd ..
rm -rf BenchhubPlus

# Optional: Remove database
sudo -u postgres psql -c "DROP DATABASE benchhub_plus;"
sudo -u postgres psql -c "DROP USER benchhub;"
```
