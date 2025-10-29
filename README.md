# BenchHub Plus
## Currently on Develop!

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

An interactive leaderboard system for dynamic LLM evaluation that converts natural language queries to customized model rankings using FastAPI backend, Streamlit frontend, Celery workers, and HRET integration.

## 🌟 Features

### 🤖 AI-Powered Evaluation Planning
- **Natural Language Interface**: Describe your evaluation needs in plain English
- **Intelligent Plan Generation**: AI converts queries to structured evaluation plans
- **Context-Aware Processing**: Understands domain-specific requirements

### 🏆 Dynamic Leaderboards
- **Real-time Rankings**: Live updates as evaluations complete
- **Multi-dimensional Comparison**: Compare models across various metrics
- **Interactive Visualizations**: Rich charts and analytics

### 🔄 Scalable Architecture
- **Async Processing**: Background task processing with Celery
- **Distributed Workers**: Scale evaluation capacity horizontally
- **Caching System**: Fast results with Redis caching

### 📊 Comprehensive Analytics
- **Multiple Metrics**: Accuracy, F1-score, semantic similarity, and more
- **Statistical Analysis**: Significance testing and confidence intervals
- **Category Breakdown**: Performance analysis by subject and difficulty

### 🐳 Production Ready
- **Docker Deployment**: Complete containerized setup
- **Health Monitoring**: Built-in health checks and monitoring
- **Scalable Design**: Ready for production workloads

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Git
- OpenAI API key (or other LLM provider API key)

### Installation & Setup

```bash
# Clone repository
git clone https://github.com/HAE-RAE/BenchhubPlus.git
cd BenchhubPlus

# Install dependencies
pip install -r requirements.txt
pip install streamlit-option-menu

# Setup environment
cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
DEFAULT_MODEL=gpt-3.5-turbo
API_BASE_URL=http://localhost:12000
FRONTEND_PORT=12001
BACKEND_PORT=12000
REDIS_PORT=6379
DATABASE_URL=sqlite:///./benchhub_plus.db
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
EOF

# Install and start Redis
sudo apt update && sudo apt install redis-server
sudo systemctl start redis-server

# Initialize database
python -c "from apps.backend.database import engine, Base; from apps.backend.models import *; Base.metadata.create_all(bind=engine)"
mkdir -p logs
```

### Start Services (4 terminals required)

```bash
# Terminal 1: Backend API
python -m uvicorn apps.backend.main:app --host 0.0.0.0 --port 12000 --reload

# Terminal 2: Frontend UI
streamlit run apps/frontend/streamlit_app.py --server.port 12001 --server.address 0.0.0.0

# Terminal 3: Celery Worker
celery -A apps.backend.celery_app worker --loglevel=info --concurrency=4

# Terminal 4: Verify services
curl http://localhost:12000/api/v1/health
```

**Access Points:**
- Frontend UI: http://localhost:12001
- Backend API: http://localhost:12000
- API Documentation: http://localhost:12000/docs

📖 **For detailed setup instructions, troubleshooting, and production deployment, see the Setup Guide ([English](./docs/eng/SETUP_GUIDE.md) | [한국어](./docs/kor/SETUP_GUIDE.md))**

## 🎯 Usage Example

### 1. Natural Language Query
```
"Compare GPT-4 and Claude-3 on Korean technology multiple choice questions"
```

### 2. Generated BenchHub Configuration
```json
{
  "problem_type": "MCQA",
  "target_type": "General",
  "subject_type": ["Technology", "Tech./Computer Science"],
  "task_type": "Knowledge",
  "external_tool_usage": false,
  "language": "Korean",
  "sample_size": 100
}
```

### 3. Model Configuration
```json
{
  "models": [
    {
      "name": "gpt-4",
      "api_base": "https://api.openai.com/v1",
      "api_key": "sk-...",
      "model_type": "openai"
    },
    {
      "name": "claude-3",
      "api_base": "https://api.anthropic.com",
      "api_key": "sk-ant-...",
      "model_type": "anthropic"
    }
  ]
}
```

### 4. Results
- Interactive leaderboard with rankings
- Detailed performance metrics by BenchHub categories
- Statistical significance analysis
- Exportable results with BenchHub metadata

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   FastAPI       │    │   Celery        │
│   Frontend      │◄──►│   Backend       │◄──►│   Workers       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       ▼
         │              ┌─────────────────┐    ┌─────────────────┐
         │              │   PostgreSQL    │    │     Redis       │
         │              │   Database      │    │     Cache       │
         └──────────────┤                 │    └─────────────────┘
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │   HRET Toolkit  │
                        │   Integration   │
                        └─────────────────┘
```

## 📚 Documentation

Documentation is available in both **English** (`docs/eng`) and **한국어** (`docs/kor`).

### Getting Started
- [📖 Installation Guide (EN)](docs/eng/installation.md) · [KO](docs/kor/installation.md) - Complete setup instructions
- [🚀 Quick Start (EN)](docs/eng/quickstart.md) · [KO](docs/kor/quickstart.md) - Get running in 5 minutes
- [👤 User Manual (EN)](docs/eng/user-manual.md) · [KO](docs/kor/user-manual.md) - Complete user guide

### Development
- [🔧 Development Guide (EN)](docs/eng/development.md) · [KO](docs/kor/development.md) - Development setup and guidelines
- [🏗️ Architecture (EN)](docs/eng/architecture.md) · [KO](docs/kor/architecture.md) - System design and architecture
- [🐳 Docker Deployment (EN)](docs/eng/docker-deployment.md) · [KO](docs/kor/docker-deployment.md) - Container deployment guide

### Reference
- [📡 API Reference (EN)](docs/eng/api-reference.md) · [KO](docs/kor/api-reference.md) - REST API documentation
- [🔧 BenchHub Configuration (EN)](docs/eng/BENCHHUB_CONFIG.md) · [KO](docs/kor/BENCHHUB_CONFIG.md) - BenchHub dataset configuration guide
- [🔗 HRET Integration (EN)](docs/eng/HRET_INTEGRATION.md) · [KO](docs/kor/HRET_INTEGRATION.md) - HRET toolkit integration guide
- [🚨 Troubleshooting (EN)](docs/eng/troubleshooting.md) · [KO](docs/kor/troubleshooting.md) - Common issues and solutions

## 🛠️ Technology Stack

### Backend
- **FastAPI**: High-performance REST API framework
- **SQLAlchemy**: Database ORM with PostgreSQL
- **Celery**: Distributed task queue with Redis
- **Pydantic**: Data validation and serialization

### Frontend
- **Streamlit**: Interactive web application framework
- **Plotly**: Interactive data visualizations
- **Pandas**: Data manipulation and analysis

### AI/ML
- **OpenAI API**: GPT models for plan generation
- **HRET Toolkit**: Evaluation framework integration
- **Custom Metrics**: Extensible evaluation metrics

### Infrastructure
- **Docker**: Containerization and deployment
- **PostgreSQL**: Primary data storage
- **Redis**: Caching and task queue
- **Nginx**: Reverse proxy (production)

## 🔧 Configuration

### Environment Variables

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here
POSTGRES_PASSWORD=secure_password

# Optional
DEBUG=false
LOG_LEVEL=info
DATABASE_URL=postgresql://user:pass@host:5432/db
CELERY_BROKER_URL=redis://host:6379/0
```

### Model Support

Currently supported model providers:
- **OpenAI**: GPT-3.5, GPT-4, and variants
- **Anthropic**: Claude models
- **Hugging Face**: Various open-source models
- **Custom**: Extensible for any API-compatible model

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/contributing.md) for details.

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/your-username/BenchhubPlus.git
cd BenchhubPlus

# Create development environment
python3.11 -m venv venv
source venv/bin/activate
pip install -e .

# Install development dependencies
pip install pytest black isort flake8 mypy

# Run tests
./scripts/test.sh

# Format code
black apps/
isort apps/
```

### Reporting Issues

- **Bug Reports**: Use the bug report template
- **Feature Requests**: Use the feature request template
- **Questions**: Start a discussion

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏  Contributors

- Hanwool Lee — [h-albert-lee](https://github.com/h-albert-lee)
- Eunsu Kim — [rladmstn1714](https://github.com/rladmstn1714)
- Joonyong Park — [JoonYong-Park](https://github.com/JoonYong-Park)
- Hyunwoo Oh - [hw-oh](https://github.com/hw-oh)

## 📞 Support

### Community Support
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community help
- **Documentation**: Comprehensive guides and references


---

**🚀 Ready to start evaluating?** Check out our [Quick Start Guide](docs/quickstart.md) or dive into the [User Manual](docs/user-manual.md)!

---

<div align="center">
  <strong>Built with ❤️ for the AI evaluation community</strong>
</div>
