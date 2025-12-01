# BenchHub Plus Documentation

Welcome to BenchHub Plus - an interactive leaderboard system for dynamic LLM evaluation that converts natural language queries to customized model rankings.

## 📚 Documentation Index

### Getting Started
- [Setup Guide](SETUP_GUIDE.md) - **Complete setup and installation instructions**
- [Installation Guide](installation.md) - Legacy installation guide
- [Quick Start](quickstart.md) - Get up and running in minutes
- [Execution Log](EXECUTION_LOG.md) - Real execution process and troubleshooting

### User Guides
- [User Manual](user-manual.md) - Complete user guide
- [API Reference](api-reference.md) - REST API documentation
- [Reflex Migration Guide](reflex-migration.md) - **New Reflex frontend usage guide**
- [Frontend Guide](frontend-guide.md) - Using the Streamlit interface (legacy)

### Development
- [Development Guide](development.md) - Development setup and guidelines
- [Architecture](architecture.md) - System architecture and design
- [Contributing](contributing.md) - How to contribute to the project

### Deployment
- [Docker Deployment](docker-deployment.md) - Docker and container deployment
- [Production Setup](production-setup.md) - Production deployment guide
- [Monitoring](monitoring.md) - System monitoring and maintenance

### Advanced Topics
- [BenchHub Configuration](BENCHHUB_CONFIG.md) - **BenchHub config structure and integration**
- [HRET Integration](HRET_INTEGRATION.md) - **HRET toolkit integration guide**
- [Custom Evaluations](custom-evaluations.md) - Creating custom evaluation plans
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

## 🚀 Quick Links

- **Live Demo**: [Demo Link] (TODO: Add demo link)
- **GitHub Repository**: [HAE-RAE/BenchhubPlus](https://github.com/HAE-RAE/BenchhubPlus)
- **Issue Tracker**: [GitHub Issues](https://github.com/HAE-RAE/BenchhubPlus/issues)
- **Discussions**: [GitHub Discussions](https://github.com/HAE-RAE/BenchhubPlus/discussions)

## 🏗️ System Overview

BenchHub Plus is a comprehensive evaluation platform that:

1. **Accepts Natural Language Queries**: Users describe their evaluation needs in plain English
2. **Generates Evaluation Plans**: AI-powered planner converts queries to structured evaluation plans
3. **Executes Evaluations**: Distributed worker system runs evaluations using HRET toolkit
4. **Provides Interactive Results**: Real-time leaderboards and detailed analysis

### Key Features

- 🤖 **AI-Powered Planning**: Natural language to evaluation plan conversion
- 🏆 **Dynamic Leaderboards**: Real-time ranking updates
- 🔄 **Async Processing**: Scalable background task processing
- 📊 **Rich Visualizations**: Interactive charts and analytics
- 🐳 **Docker Ready**: Complete containerized deployment
- 🔌 **Extensible**: Plugin architecture for custom evaluations

## 🛠️ Technology Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: Streamlit, Plotly
- **Task Queue**: Celery, Redis
- **Evaluation**: HRET Toolkit
- **Deployment**: Docker, Docker Compose
- **AI/ML**: OpenAI API, Custom LLM Integration

## 📖 Getting Help

- **Documentation Issues**: Open an issue with the `documentation` label
- **Bug Reports**: Use the bug report template
- **Feature Requests**: Use the feature request template
- **General Questions**: Start a discussion

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

