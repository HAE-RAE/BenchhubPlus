# BenchHub Plus
## Currently on Develop!

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

An interactive leaderboard system for dynamic LLM evaluation that converts natural language queries to customized model rankings using FastAPI backend, modern Reflex frontend, Celery workers, and HRET integration.

<img width="1919" height="962" alt="benchhubplus" src="https://github.com/user-attachments/assets/0628747f-0939-4090-b5f3-ebb43c8c25a7" />

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

## ✨ What's New: Reflex Frontend

We've migrated from Streamlit to **Reflex** for a modern, production-ready web experience! 

### 🆕 Reflex Benefits
- **Modern UI/UX**: Clean, responsive design with Tailwind CSS
- **Better Performance**: Optimized rendering and state management  
- **Production Ready**: Built for scalability and deployment
- **Component Architecture**: Maintainable and extensible codebase

### 🔄 Migration Status
- ✅ **Reflex Frontend**: Full-featured modern interface (recommended)
- 🔧 **Streamlit Frontend**: Legacy support maintained for compatibility

## 🚀 Quick Start

### Recommended: Docker-based setup

1. **Install prerequisites**
   - Git
   - Docker and Docker Compose
   - An OpenAI API key (or another supported model provider key)

2. **Clone the repository and create your environment file**

   ```bash
   git clone https://github.com/HAE-RAE/BenchhubPlus.git
   cd BenchhubPlus
   cp .env.example .env
   ```

3. **Fill in the required variables**
   - `OPENAI_API_KEY`: your model provider key
   - `POSTGRES_PASSWORD`: choose a strong password for the bundled PostgreSQL database
   - Adjust any other values (ports, planner model, etc.) if needed

4. **Launch the full stack**

   ```bash
   # Option 1: Streamlit frontend (legacy)
   ./scripts/deploy.sh development
   
   # Option 2: Reflex frontend (modern, recommended)
   docker-compose -f docker-compose.reflex.yml up --build
   ```

   The helper script builds the images, starts the services, and waits for them to report healthy.

5. **Open the application**
   - Frontend UI: http://localhost:8502 (Streamlit) or http://localhost:12000 (Reflex)
   - Backend API: http://localhost:8001
   - API documentation: http://localhost:8001/docs
   - Flower (Celery dashboard): http://localhost:5556

6. **Verify everything is running**

   ```bash
   curl http://localhost:8001/api/v1/health
   ```

7. **Shut down when finished**

   ```bash
   docker-compose -f docker-compose.dev.yml down
   ```

### Alternative: Local Python environment

For contributors who prefer not to use Docker:

```bash
./scripts/setup.sh         # creates a Python 3.11 virtualenv and installs dependencies
source venv/bin/activate
python -m uvicorn apps.backend.main:app --host 0.0.0.0 --port 8000 --reload

# Choose your frontend:
# Option 1: Streamlit (legacy)
streamlit run apps/frontend/streamlit_app.py --server.port 8501 --server.address 0.0.0.0

# Option 2: Reflex (modern, recommended)
cd apps/reflex_frontend && reflex run --env dev --backend-host 0.0.0.0 --frontend-port 12000

# Background worker
celery -A apps.worker.celery_app worker --loglevel=info
```

You will also need local PostgreSQL and Redis instances that match the connection settings in `.env`.

📖 **Need more detail?** The [Quick Start Guide](./docs/eng/quickstart.md) walks through the process with screenshots and tips, and the [User Manual](./docs/eng/user-manual.md) explains how to operate the app end to end. Setup guides are also available ([English](./docs/eng/SETUP_GUIDE.md) | [한국어](./docs/kor/SETUP_GUIDE.md)).

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
  "subject_type": ["Tech.", "Tech./Coding"],
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
│     Reflex      │    │   FastAPI       │    │   Celery        │
│   Frontend      │◄──►│   Backend       │◄──►│   Workers       │
│  (+ Streamlit)  │    │                 │    │                 │
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
- **Reflex**: Modern Python web framework (recommended)
- **Streamlit**: Interactive web application framework (legacy support)
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
