#!/bin/bash

# BenchHub Plus Setup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Setting up BenchHub Plus development environment${NC}"

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${RED}❌ Python 3.11+ is required. Current version: $python_version${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python version: $python_version${NC}"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}🐍 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}🔄 Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}📦 Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
pip install -e .

# Create directories
echo -e "${YELLOW}📁 Creating directories...${NC}"
mkdir -p logs
mkdir -p data
mkdir -p ssl
mkdir -p temp

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file with your configuration${NC}"
fi

# Initialize database (if PostgreSQL is available)
echo -e "${YELLOW}🗄️  Checking database connection...${NC}"
if python3 -c "
import os
from apps.core.db import init_db
try:
    init_db()
    print('✅ Database initialized successfully')
except Exception as e:
    print(f'⚠️  Database initialization failed: {e}')
    print('💡 Make sure PostgreSQL is running or use Docker setup')
" 2>/dev/null; then
    echo -e "${GREEN}Database setup completed${NC}"
else
    echo -e "${YELLOW}Database setup skipped (will be handled by Docker)${NC}"
fi

# Create sample configuration files
echo -e "${YELLOW}📄 Creating sample configuration files...${NC}"

# Sample plan.yaml
cat > sample_plan.yaml << 'EOF'
version: "1.0"
metadata:
  name: "Sample Evaluation Plan"
  description: "Sample plan for testing BenchHub Plus"
  language: "English"
  subject_type: "General"
  task_type: "QA"
  sample_size: 50

models:
  - name: "gpt-3.5-turbo"
    api_base: "https://api.openai.com/v1"
    api_key: "${OPENAI_API_KEY}"
    model_type: "openai"
    temperature: 0.7
    max_tokens: 1024

datasets:
  - name: "sample_dataset"
    type: "qa"
    source: "local"
    path: "data/sample_questions.json"

evaluation:
  metrics:
    - "accuracy"
    - "f1_score"
  timeout: 30
  batch_size: 10
EOF

# Sample questions
cat > data/sample_questions.json << 'EOF'
[
  {
    "id": 1,
    "question": "What is the capital of France?",
    "answer": "Paris",
    "category": "geography"
  },
  {
    "id": 2,
    "question": "What is 2 + 2?",
    "answer": "4",
    "category": "math"
  },
  {
    "id": 3,
    "question": "Who wrote Romeo and Juliet?",
    "answer": "William Shakespeare",
    "category": "literature"
  }
]
EOF

# Create development scripts
echo -e "${YELLOW}📜 Creating development scripts...${NC}"

# Backend development script
cat > scripts/dev-backend.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
export PYTHONPATH=$PWD:$PYTHONPATH
uvicorn apps.backend.main:app --host 0.0.0.0 --port 8000 --reload
EOF

# Worker development script
cat > scripts/dev-worker.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
export PYTHONPATH=$PWD:$PYTHONPATH
celery -A apps.worker.celery_app worker --loglevel=info --concurrency=2
EOF

# Frontend development script
cat > scripts/dev-frontend.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
export PYTHONPATH=$PWD:$PYTHONPATH
streamlit run apps/frontend/streamlit_app.py --server.port=8501
EOF

# Make scripts executable
chmod +x scripts/dev-*.sh

# Create test script
cat > scripts/test.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
export PYTHONPATH=$PWD:$PYTHONPATH

echo "🧪 Running tests..."

# Run unit tests
python -m pytest tests/ -v

# Run integration tests
python -m pytest tests/integration/ -v

# Run API tests
python -m pytest tests/api/ -v

echo "✅ All tests completed"
EOF

chmod +x scripts/test.sh

# Create quick start guide
cat > QUICKSTART.md << 'EOF'
# BenchHub Plus Quick Start

## Development Setup

1. **Setup environment:**
   ```bash
   ./scripts/setup.sh
   ```

2. **Configure environment:**
   Edit `.env` file with your API keys and database settings.

3. **Start services:**

   **Option A: Docker (Recommended)**
   ```bash
   ./scripts/deploy.sh development
   ```

   **Option B: Local Development**
   ```bash
   # Terminal 1: Backend
   ./scripts/dev-backend.sh
   
   # Terminal 2: Worker
   ./scripts/dev-worker.sh
   
   # Terminal 3: Frontend
   ./scripts/dev-frontend.sh
   ```

4. **Access services:**
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Usage

1. Open the frontend at http://localhost:8501
2. Enter a natural language query (e.g., "Compare these models on math problems")
3. Configure your models with API keys
4. Start evaluation and monitor progress
5. View results in the leaderboard

## Testing

```bash
./scripts/test.sh
```

## Troubleshooting

- Check logs: `docker-compose logs -f [service]`
- Restart services: `docker-compose restart`
- Clean reset: `docker-compose down -v && docker-compose up -d`
EOF

echo -e "${GREEN}🎉 Setup completed successfully!${NC}"
echo -e "${BLUE}📋 Next steps:${NC}"
echo -e "  1. Edit .env file with your configuration"
echo -e "  2. Run: ${GREEN}./scripts/deploy.sh development${NC}"
echo -e "  3. Open: ${GREEN}http://localhost:8502${NC}"
echo -e ""
echo -e "${BLUE}📖 See QUICKSTART.md for detailed instructions${NC}"