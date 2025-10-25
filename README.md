# BenchHub Plus

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

### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/HAE-RAE/BenchhubPlus.git
cd BenchhubPlus

# Setup and deploy
./scripts/setup.sh
cp .env.example .env
# Edit .env with your API keys
./scripts/deploy.sh development
```

**Access Points:**
- Frontend: http://localhost:8502
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

### Option 2: Local Development

```bash
# Clone and setup
git clone https://github.com/HAE-RAE/BenchhubPlus.git
cd BenchhubPlus

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .

# Setup database and Redis
# (See installation guide for details)

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start services
./scripts/dev-backend.sh    # Terminal 1
./scripts/dev-worker.sh     # Terminal 2
./scripts/dev-frontend.sh   # Terminal 3
```

## 🎯 Usage Example

### 1. Natural Language Query
```
"Compare GPT-4 and Claude-3 on Korean high school math problems"
```

### 2. Model Configuration
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

### 3. Results
- Interactive leaderboard with rankings
- Detailed performance metrics
- Statistical significance analysis
- Exportable results

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

### Getting Started
- [📖 Installation Guide](docs/installation.md) - Complete setup instructions
- [🚀 Quick Start](docs/quickstart.md) - Get running in 5 minutes
- [👤 User Manual](docs/user-manual.md) - Complete user guide

### Development
- [🔧 Development Guide](docs/development.md) - Development setup and guidelines
- [🏗️ Architecture](docs/architecture.md) - System design and architecture
- [🐳 Docker Deployment](docs/docker-deployment.md) - Container deployment guide

### Reference
- [📡 API Reference](docs/api-reference.md) - REST API documentation
- [🚨 Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

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

## 📊 Evaluation Metrics

### Built-in Metrics
- **Accuracy**: Exact match accuracy
- **F1 Score**: Harmonic mean of precision and recall
- **Semantic Similarity**: Embedding-based similarity
- **BLEU Score**: N-gram based similarity
- **Custom Metrics**: Define your own evaluation criteria

### Statistical Analysis
- **Significance Testing**: Statistical significance of differences
- **Confidence Intervals**: Uncertainty quantification
- **Effect Size**: Practical significance measurement

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

## 🙏 Acknowledgments

- **HRET Toolkit**: Evaluation framework foundation
- **OpenAI**: Language model capabilities
- **FastAPI & Streamlit**: Excellent web frameworks
- **Open Source Community**: Various libraries and tools

## 📞 Support

### Community Support
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community help
- **Documentation**: Comprehensive guides and references

### Professional Support
- **Enterprise Support**: Available for production deployments
- **Custom Development**: Tailored solutions and integrations
- **Training**: Team training and onboarding

---

**🚀 Ready to start evaluating?** Check out our [Quick Start Guide](docs/quickstart.md) or dive into the [User Manual](docs/user-manual.md)!

---

<div align="center">
  <strong>Built with ❤️ for the AI evaluation community</strong>
</div>
