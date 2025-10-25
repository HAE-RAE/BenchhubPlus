# Quick Start Guide

Get BenchHub Plus up and running in minutes with this quick start guide.

## 🚀 5-Minute Setup

### Prerequisites
- Docker and Docker Compose installed
- OpenAI API key (or other model API keys)

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/HAE-RAE/BenchhubPlus.git
cd BenchhubPlus

# Run the setup script
./scripts/setup.sh
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
nano .env
```

**Required settings:**
```env
OPENAI_API_KEY=your_openai_api_key_here
POSTGRES_PASSWORD=secure_password_here
```

### Step 3: Deploy

```bash
# Start all services
./scripts/deploy.sh development
```

### Step 4: Access the Application

- **Frontend**: http://localhost:8502
- **API Documentation**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/api/v1/health

## 🎯 First Evaluation

### 1. Open the Web Interface

Navigate to http://localhost:8502 in your browser.

### 2. Create Your First Evaluation

1. **Go to the "Evaluate" tab**
2. **Enter a query**: "Compare GPT-4 on basic math problems"
3. **Configure your model**:
   - Name: `gpt-4`
   - API Base: `https://api.openai.com/v1`
   - API Key: Your OpenAI API key
   - Model Type: `openai`
4. **Click "🚀 Start Evaluation"**

### 3. Monitor Progress

1. **Switch to the "Status" tab**
2. **Watch your evaluation progress**
3. **View results when complete**

### 4. Browse Results

1. **Go to the "Browse" tab**
2. **Explore your leaderboard results**
3. **Filter and sort as needed**

## 📊 Example Queries

Try these example queries to get started:

### Basic Examples
```
"Test basic math skills with simple arithmetic"
"Compare reading comprehension in English"
"Evaluate code generation for Python"
```

### Advanced Examples
```
"Compare these models on Korean high school math problems"
"Evaluate scientific reasoning in chemistry and physics"
"Test creative writing abilities with storytelling prompts"
```

## 🔧 Common Configuration

### Multiple Models

To compare multiple models, add more model configurations:

```json
{
  "query": "Compare multiple models on math problems",
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

### Custom Evaluation Criteria

Fine-tune your evaluation:

- **Language**: English, Korean, etc.
- **Subject**: Math, Science, Literature, etc.
- **Difficulty**: Elementary, High School, University
- **Sample Size**: 10-1000 samples
- **Metrics**: Accuracy, F1 Score, etc.

## 🚨 Troubleshooting

### Service Won't Start

```bash
# Check Docker status
docker --version
docker-compose --version

# View logs
docker-compose logs -f
```

### API Key Issues

1. **Verify your API key is correct**
2. **Check API key permissions**
3. **Ensure sufficient credits/quota**

### Slow Performance

1. **Start with smaller sample sizes (10-50)**
2. **Check your internet connection**
3. **Monitor API rate limits**

### Database Issues

```bash
# Reset database
docker-compose down -v
docker-compose up -d
```

## 📚 Next Steps

### Learn More
- [User Manual](user-manual.md) - Complete usage guide
- [API Reference](api-reference.md) - REST API documentation
- [Development Guide](development.md) - Development setup

### Advanced Features
- **Custom Datasets**: Upload your own evaluation data
- **Batch Evaluations**: Run multiple evaluations simultaneously
- **Custom Metrics**: Define specialized evaluation criteria
- **Export Results**: Download results for analysis

### Integration
- **API Integration**: Use the REST API in your applications
- **Webhook Support**: Get notified when evaluations complete
- **Custom Models**: Add support for new model providers

## 🤝 Getting Help

### Quick Help
- **System Status**: Check the "System" tab in the web interface
- **Logs**: View Docker logs with `docker-compose logs -f`
- **Health Check**: Visit http://localhost:8001/api/v1/health

### Community Support
- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share experiences
- **Documentation**: Browse the complete documentation

### Professional Support
- **Enterprise Support**: Available for production deployments
- **Custom Development**: Tailored solutions for specific needs
- **Training**: Team training and onboarding sessions

---

**🎉 Congratulations!** You now have BenchHub Plus running and can start evaluating language models. Explore the interface, try different queries, and see how your models perform!

*For detailed information about any feature, check the complete [User Manual](user-manual.md) or [API Reference](api-reference.md).*