# BenchHub Plus Setup Guide

This guide provides step-by-step instructions for setting up and running the BenchHub Plus application.

## Prerequisites

- Python 3.8+
- Git
- OpenAI API key (or other LLM provider API key)
- **Seed Data File**: `seeds/seed_data.parquet` (see [Database Seeding](#database-seeding) section)

## Quick Start

### 1. Clone and Navigate to Repository

```bash
git clone https://github.com/HAE-RAE/BenchhubPlus.git
cd BenchhubPlus
```

### 2. Environment Setup

Create a `.env` file in the root directory:

```bash
# API Configuration
OPENAI_API_KEY=your_openai_api_key_here
DEFAULT_MODEL=gpt-3.5-turbo

# Service Ports
API_BASE_URL=http://localhost:12000
FRONTEND_PORT=12001
BACKEND_PORT=12000
REDIS_PORT=6379

# Database
DATABASE_URL=sqlite:///./benchhub_plus.db

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 3. Install Dependencies

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Install additional required packages:

```bash
pip install streamlit-option-menu
```

### 4. Install and Start Redis Server

#### On Ubuntu/Debian:
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### On macOS:
```bash
brew install redis
brew services start redis
```

#### On Windows:
Download and install Redis from the official website or use WSL.

Verify Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

### 5. Database Seeding

BenchHub Plus uses a Parquet-based database seeding system for efficient initialization. The system automatically loads pre-aggregated benchmark data from `seeds/seed_data.parquet` when the application starts.

#### Prepare Seed Data File

**Important**: You need to create the `seeds/seed_data.parquet` file before running the application. This file should contain pre-aggregated benchmark results with the following schema:

| Column | Type | Description |
|--------|------|-------------|
| `model_name` | string | Model identifier (e.g., "Qwen_Qwen2.5-72B-Instruct") |
| `language` | string | Evaluation language ("Korean" or "English") |
| `subject_type` | string | Subject category (e.g., "HASS/Economics", "Tech./Coding") |
| `task_type` | string | Task type (e.g., "Knowledge", "Reasoning") |
| `score` | float64 | Aggregated performance score (0.0 to 1.0) |

#### Create Seed Data Directory

```bash
mkdir -p seeds
```

#### Generate Seed Data (Example)

If you have raw evaluation results in JSONL format, you can aggregate them into the required Parquet format:

```python
import pandas as pd

# Example: Load and aggregate your evaluation results
# Replace this with your actual data processing logic
data = [
    {
        'model_name': 'GPT-4',
        'language': 'English',
        'subject_type': 'HASS/Economics',
        'task_type': 'Knowledge',
        'score': 0.85
    },
    # ... more records
]

df = pd.DataFrame(data)
df.to_parquet('seeds/seed_data.parquet', index=False)
print(f"Seed file created with {len(df)} records")
```

#### Initialize Database

Create the SQLite database and required tables:

```bash
python -c "
from apps.core.db import engine, Base
Base.metadata.create_all(bind=engine)
print('Database initialized successfully')
"
```

Create logs directory:
```bash
mkdir -p logs
```

**Note**: The database will be automatically seeded with data from `seeds/seed_data.parquet` when the backend service starts. If the seed file is missing, the application will start normally but with an empty leaderboard.

### 6. Start Services

You need to start multiple services. Open separate terminal windows/tabs for each:

#### Terminal 1: Backend Server
```bash
cd BenchhubPlus
python -m uvicorn apps.backend.main:app --host 0.0.0.0 --port 12000 --reload
```

#### Terminal 2: Frontend (Streamlit)
```bash
cd BenchhubPlus
streamlit run apps/frontend/streamlit_app.py --server.port 12001 --server.address 0.0.0.0
```

#### Terminal 3: Celery Worker
```bash
cd BenchhubPlus
celery -A apps.backend.celery_app worker --loglevel=info --concurrency=4
```

### 7. Verify Installation

1. **Backend Health Check:**
   ```bash
   curl http://localhost:12000/api/v1/health
   ```
   Should return: `{"status":"healthy","timestamp":"...","version":"2.0.0","database_status":"connected","redis_status":"connected"}`

2. **Frontend Access:**
   Open your browser and navigate to: `http://localhost:12001`

3. **Redis Status:**
   ```bash
   redis-cli ping
   ```

## Service Architecture

The BenchHub Plus application consists of four main components:

1. **Backend API (FastAPI)** - Port 12000
   - Handles API requests
   - Manages database operations
   - Coordinates evaluation tasks

2. **Frontend UI (Streamlit)** - Port 12001
   - User interface for evaluation requests
   - Real-time status monitoring
   - Results visualization

3. **Task Queue (Celery + Redis)** - Port 6379
   - Asynchronous task processing
   - Evaluation job management
   - Background processing

4. **Database (SQLite)**
   - Stores evaluation results
   - Caches leaderboard data
   - Manages experiment samples

## Troubleshooting

### Common Issues and Solutions

#### 1. Redis Connection Error
```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379
```
**Solution:** Ensure Redis server is running:
```bash
sudo systemctl start redis-server  # Linux
brew services start redis          # macOS
```

#### 2. Database Connection Error
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table
```
**Solution:** Initialize the database:
```bash
python -c "from apps.backend.database import engine, Base; from apps.backend.models import *; Base.metadata.create_all(bind=engine)"
```

#### 3. Missing Dependencies
```
ModuleNotFoundError: No module named 'streamlit_option_menu'
```
**Solution:** Install missing packages:
```bash
pip install streamlit-option-menu
```

#### 4. Port Already in Use
```
OSError: [Errno 98] Address already in use
```
**Solution:** Kill existing processes or use different ports:
```bash
# Find and kill process using port 12000
lsof -ti:12000 | xargs kill -9

# Or change ports in .env file
```

#### 5. OpenAI API Key Error
```
openai.error.AuthenticationError: Incorrect API key provided
```
**Solution:** Verify your API key in the `.env` file and ensure it's valid.

### Service Status Check

Use this script to check all services:

```bash
#!/bin/bash
echo "=== BenchHub Plus Service Status ==="

# Check Redis
echo -n "Redis: "
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not running"
fi

# Check Backend
echo -n "Backend: "
if curl -s http://localhost:12000/api/v1/health > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not running"
fi

# Check Frontend
echo -n "Frontend: "
if curl -s http://localhost:12001 > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not running"
fi

# Check Database
echo -n "Database: "
if [ -f "./benchhub_plus.db" ]; then
    echo "✅ Exists"
else
    echo "❌ Not found"
fi
```

## Development Mode

For development, you can use the `--reload` flag for auto-reloading:

```bash
# Backend with auto-reload
python -m uvicorn apps.backend.main:app --host 0.0.0.0 --port 12000 --reload

# Streamlit with auto-reload (default behavior)
streamlit run apps/frontend/streamlit_app.py --server.port 12001
```

## Production Deployment

For production deployment, consider:

1. Use a production WSGI server (e.g., Gunicorn)
2. Set up proper logging
3. Use PostgreSQL instead of SQLite
4. Configure Redis persistence
5. Set up monitoring and health checks
6. Use environment-specific configuration files

## Next Steps

After successful setup:

1. Configure your LLM models in the UI
2. Create evaluation requests
3. Monitor results in the Status tab
4. Browse historical evaluations in the Browse tab
5. Check system status in the System tab

For more information, see:
- [Configuration Guide](./CONFIGURATION.md)
- [API Documentation](./API.md)
- [BenchHub Integration](./BENCHHUB_INTEGRATION.md)