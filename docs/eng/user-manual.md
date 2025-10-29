# User Manual

This comprehensive guide covers all aspects of using BenchHub Plus for LLM evaluation.

## 🎯 Overview

BenchHub Plus allows you to evaluate and compare language models using natural language queries. Simply describe what you want to test, configure your models, and get comprehensive evaluation results.

## 🚀 Getting Started

### Accessing the Application

1. **Open your web browser**
2. **Navigate to the application URL**:
   - Local development: http://localhost:8501
   - Production: Your deployed URL

### Interface Overview

The application has four main sections:

- **🎮 Evaluate**: Create and submit new evaluations
- **📊 Status**: Monitor evaluation progress
- **🔍 Browse**: Explore historical leaderboards
- **⚙️ System**: Check system health and statistics

## 📝 Creating Evaluations

### Step 1: Natural Language Query

In the **Evaluate** tab, start by describing your evaluation needs:

**Example queries:**
```
"Compare these models on Korean math problems for high school students"

"Evaluate language understanding capabilities in English literature"

"Test code generation abilities for Python programming tasks"

"Compare logical reasoning performance on complex problems"

"Evaluate translation quality between English and Korean"
```

**Query Tips:**
- Be specific about the subject area (math, science, literature, etc.)
- Mention the target language if relevant
- Specify difficulty level (elementary, high school, university, etc.)
- Include task type (QA, generation, reasoning, etc.)

### Step 2: Model Configuration

Configure the models you want to evaluate:

#### Basic Configuration
- **Model Name**: Unique identifier (e.g., "gpt-4", "claude-3")
- **API Base URL**: Model API endpoint
- **API Key**: Authentication key for the model
- **Model Type**: Select from supported types (OpenAI, Anthropic, etc.)

#### Advanced Settings
- **Temperature**: Sampling randomness (0.0-2.0)
- **Max Tokens**: Maximum response length
- **Timeout**: Request timeout in seconds

#### Multiple Models
- Use the "Number of models" selector to add more models
- Each model needs complete configuration
- Maximum 10 models per evaluation

### Step 3: Evaluation Criteria (Optional)

Fine-tune your evaluation with specific criteria:

- **Language**: Target language for evaluation
- **Subject Type**: Domain area (Math, Science, etc.)
- **Task Type**: Type of evaluation (QA, Classification, etc.)
- **Difficulty Level**: Complexity of questions
- **Sample Size**: Number of test samples (10-1000)
- **Metrics**: Evaluation metrics to calculate

### Step 4: Submit Evaluation

1. **Review your configuration**
2. **Click "🚀 Start Evaluation"**
3. **Note the Task ID** for tracking
4. **Monitor progress** in the Status tab

## 📊 Monitoring Progress

### Task Status

In the **Status** tab, you can:

- **View current task progress**
- **See task history**
- **Monitor system status**
- **Access detailed results**

### Status Indicators

- 🟡 **PENDING**: Task is queued
- 🔵 **STARTED**: Task is running
- 🟢 **SUCCESS**: Task completed successfully
- 🔴 **FAILURE**: Task failed

### Real-time Updates

The status page automatically refreshes for running tasks. You can also manually refresh using the "🔄 Refresh Status" button.

## 🏆 Understanding Results

### Leaderboard View

Results are displayed as an interactive leaderboard showing:

- **Model rankings** by performance
- **Scores** with statistical significance
- **Accuracy metrics**
- **Sample counts**
- **Execution times**

### Visualizations

#### Performance Comparison
- **Bar charts** showing relative performance
- **Color-coded** results for easy comparison
- **Sortable tables** with detailed metrics

#### Multi-dimensional Analysis
- **Radar charts** for multiple metrics
- **Score distributions** across samples
- **Time series** for performance trends

### Detailed Results

Expand the "Detailed Results" section to see:
- **Raw evaluation data**
- **Individual sample results**
- **Error analysis**
- **Statistical breakdowns**

## 🔍 Browsing Historical Data

### Leaderboard Browser

Use the **Browse** tab to explore past evaluations:

#### Filtering Options
- **Language**: Filter by target language
- **Subject**: Filter by domain area
- **Task Type**: Filter by evaluation type
- **Date Range**: Filter by time period
- **Score Range**: Filter by performance range

#### Search Results
- **Ranked listings** of all matching evaluations
- **Sortable columns** for different metrics
- **Visual charts** of top performers
- **Export options** for data analysis

### Historical Trends

Track model performance over time:
- **Performance evolution** of specific models
- **Comparative trends** across different domains
- **Benchmark stability** analysis

## ⚙️ System Management

### Health Monitoring

The **System** tab provides:

#### Service Status
- **Database connectivity**
- **Redis cache status**
- **API availability**
- **Worker health**

#### System Statistics
- **Task queue status**
- **Cache utilization**
- **Performance metrics**
- **Resource usage**

### Troubleshooting

If you encounter issues:

1. **Check system status** first
2. **Review error messages** in task details
3. **Verify model configurations**
4. **Check API key validity**
5. **Contact support** if problems persist

## 🔧 Advanced Features

### Query Templates

Use pre-built templates for common evaluation scenarios:

- **Math Comparison**: Mathematical problem solving
- **Language Understanding**: Comprehension tasks
- **Code Generation**: Programming tasks
- **Reasoning Tasks**: Logical reasoning
- **Translation Quality**: Language translation

### Batch Operations

For large-scale evaluations:

1. **Prepare model configurations** in JSON/CSV format
2. **Upload batch files** using the batch upload feature
3. **Submit multiple evaluations** simultaneously
4. **Monitor progress** across all tasks

### Custom Evaluations

Advanced users can:
- **Define custom metrics**
- **Upload custom datasets**
- **Configure specialized evaluation plans**
- **Integrate with external tools**

## 📊 Best Practices

### Query Writing
- **Be specific** about requirements
- **Include context** about the domain
- **Specify constraints** (language, difficulty, etc.)
- **Use clear, descriptive language**

### Model Configuration
- **Use descriptive names** for easy identification
- **Test with small samples** first
- **Keep API keys secure**
- **Monitor usage costs**

### Result Interpretation
- **Consider sample sizes** for statistical significance
- **Compare similar evaluation conditions**
- **Look at multiple metrics** for comprehensive analysis
- **Account for model-specific strengths**

## 🚨 Common Issues

### Evaluation Failures

**Possible causes:**
- Invalid API keys
- Network connectivity issues
- Model API rate limits
- Insufficient credits/quota

**Solutions:**
- Verify API key validity
- Check network connection
- Reduce concurrent requests
- Monitor API usage limits

### Slow Performance

**Possible causes:**
- Large sample sizes
- Complex evaluation queries
- High system load
- Network latency

**Solutions:**
- Start with smaller samples
- Simplify evaluation criteria
- Check system resources
- Try during off-peak hours

### Unexpected Results

**Possible causes:**
- Ambiguous queries
- Model-specific behaviors
- Dataset characteristics
- Evaluation metric limitations

**Solutions:**
- Refine query specificity
- Compare with known benchmarks
- Analyze individual samples
- Try different metrics

## 📞 Getting Help

### Documentation
- **User Manual**: This document
- **API Reference**: Technical API documentation
- **Troubleshooting Guide**: Common issues and solutions
- **FAQ**: Frequently asked questions

### Support Channels
- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Community Q&A
- **Email Support**: Direct technical support
- **Documentation Issues**: Report documentation problems

### Community Resources
- **Example Queries**: Community-shared evaluation examples
- **Best Practices**: User-contributed tips and tricks
- **Use Cases**: Real-world application examples
- **Integration Guides**: Third-party tool integrations

## 🔄 Updates and Maintenance

### System Updates
- **Automatic updates** for minor improvements
- **Notification system** for major changes
- **Backward compatibility** for existing evaluations
- **Migration guides** for breaking changes

### Data Management
- **Automatic cleanup** of old evaluation data
- **Export options** for important results
- **Backup recommendations** for critical data
- **Privacy controls** for sensitive evaluations

---

*For technical support or questions about this user manual, please contact our support team or visit our documentation repository.*