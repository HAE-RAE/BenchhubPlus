# API Reference

Complete reference for the BenchHub Plus REST API.

## 🌐 Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

All API endpoints are prefixed with `/api/v1`.

## 🔐 Authentication

Currently, the API uses API key authentication for external model services. Future versions will include user authentication.

```http
Authorization: Bearer your-api-key
```

## 📋 API Endpoints

### Health Check

#### GET /api/v1/health

Check system health status.

**Response:**
```json
{
  "status": "healthy",
  "database_status": "connected",
  "redis_status": "connected",
  "planner_available": true,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Status Codes:**
- `200`: System is healthy
- `503`: System has issues

---

### Leaderboard Management

#### POST /api/v1/leaderboard/generate

Generate a new leaderboard based on natural language query.

**Request Body:**
```json
{
  "query": "Compare these models on Korean math problems for high school students",
  "models": [
    {
      "name": "gpt-4",
      "api_base": "https://api.openai.com/v1",
      "api_key": "sk-...",
      "model_type": "openai",
      "temperature": 0.7,
      "max_tokens": 1024,
      "timeout": 30
    }
  ],
  "criteria": {
    "language": "Korean",
    "subject_type": "Math",
    "task_type": "QA",
    "difficulty": "High School",
    "sample_size": 100,
    "metrics": ["accuracy", "f1_score"]
  }
}
```

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PENDING",
  "message": "Evaluation task created successfully",
  "estimated_duration": 300
}
```

**Status Codes:**
- `200`: Task created successfully
- `400`: Invalid request data
- `422`: Validation error
- `500`: Internal server error

#### GET /api/v1/leaderboard/browse

Browse existing leaderboard entries with filtering.

**Query Parameters:**
- `language` (optional): Filter by language
- `subject_type` (optional): Filter by subject
- `task_type` (optional): Filter by task type
- `limit` (optional): Maximum results (default: 100)
- `offset` (optional): Pagination offset (default: 0)
- `sort_by` (optional): Sort field (default: "score")
- `sort_order` (optional): "asc" or "desc" (default: "desc")
- `date_from` (optional): Filter from date (ISO format)
- `date_to` (optional): Filter to date (ISO format)
- `score_min` (optional): Minimum score filter
- `score_max` (optional): Maximum score filter

**Example Request:**
```http
GET /api/v1/leaderboard/browse?language=Korean&subject_type=Math&limit=50
```

**Response:**
```json
{
  "entries": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "model_name": "gpt-4",
      "score": 0.92,
      "accuracy": 0.89,
      "language": "Korean",
      "subject_type": "Math",
      "task_type": "QA",
      "sample_count": 100,
      "last_updated": "2024-01-15T10:30:00Z",
      "metadata": {
        "difficulty": "High School",
        "evaluation_time": 245.6
      }
    }
  ],
  "total": 150,
  "page": 1,
  "pages": 3,
  "has_next": true,
  "has_prev": false
}
```

**Status Codes:**
- `200`: Success
- `400`: Invalid query parameters
- `500`: Internal server error

---

### Task Management

#### GET /api/v1/tasks/{task_id}

Get detailed information about a specific task.

**Path Parameters:**
- `task_id`: UUID of the task

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "SUCCESS",
  "created_at": "2024-01-15T10:00:00Z",
  "started_at": "2024-01-15T10:01:00Z",
  "completed_at": "2024-01-15T10:05:30Z",
  "progress": 100,
  "result": {
    "model_results": [
      {
        "model_name": "gpt-4",
        "average_score": 0.92,
        "accuracy": 0.89,
        "total_samples": 100,
        "execution_time": 245.6,
        "detailed_metrics": {
          "f1_score": 0.91,
          "precision": 0.93,
          "recall": 0.88
        }
      }
    ],
    "evaluation_metadata": {
      "language": "Korean",
      "subject_type": "Math",
      "task_type": "QA",
      "total_duration": 330.2
    }
  },
  "error_message": null
}
```

**Status Codes:**
- `200`: Task found
- `404`: Task not found
- `500`: Internal server error

#### DELETE /api/v1/tasks/{task_id}

Cancel a pending or running task.

**Path Parameters:**
- `task_id`: UUID of the task

**Response:**
```json
{
  "message": "Task cancelled successfully",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "previous_status": "STARTED"
}
```

**Status Codes:**
- `200`: Task cancelled
- `404`: Task not found
- `409`: Task cannot be cancelled (already completed)
- `500`: Internal server error

#### GET /api/v1/tasks

List all tasks with filtering options.

**Query Parameters:**
- `status` (optional): Filter by status (PENDING, STARTED, SUCCESS, FAILURE)
- `limit` (optional): Maximum results (default: 50)
- `offset` (optional): Pagination offset (default: 0)
- `user_id` (optional): Filter by user (future feature)

**Response:**
```json
{
  "tasks": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "SUCCESS",
      "created_at": "2024-01-15T10:00:00Z",
      "completed_at": "2024-01-15T10:05:30Z",
      "query": "Compare models on math problems",
      "model_count": 2,
      "progress": 100
    }
  ],
  "total": 25,
  "page": 1,
  "pages": 1,
  "has_next": false,
  "has_prev": false
}
```

---

### System Statistics

#### GET /api/v1/stats

Get system statistics and metrics.

**Response:**
```json
{
  "tasks": {
    "PENDING": 5,
    "STARTED": 2,
    "SUCCESS": 150,
    "FAILURE": 3
  },
  "cache_entries": 1250,
  "models_evaluated": 25,
  "total_evaluations": 160,
  "average_evaluation_time": 245.6,
  "system_uptime": 86400,
  "planner_available": true,
  "worker_status": {
    "active": 2,
    "total": 4
  }
}
```

**Status Codes:**
- `200`: Success
- `500`: Internal server error

---

### Planner Service

#### POST /api/v1/planner/generate-plan

Generate evaluation plan from natural language query.

**Request Body:**
```json
{
  "query": "Compare these models on Korean math problems for high school students",
  "context": {
    "models": ["gpt-4", "claude-3"],
    "preferred_metrics": ["accuracy", "f1_score"],
    "sample_size_preference": "medium"
  }
}
```

**Response:**
```json
{
  "plan": {
    "version": "1.0",
    "metadata": {
      "name": "Korean Math Evaluation",
      "description": "Evaluation of models on Korean high school math problems",
      "language": "Korean",
      "subject_type": "Math",
      "task_type": "QA",
      "sample_size": 100
    },
    "evaluation": {
      "metrics": ["accuracy", "f1_score"],
      "timeout": 30,
      "batch_size": 10
    },
    "datasets": [
      {
        "name": "korean_math_hs",
        "type": "qa",
        "source": "hret",
        "filters": {
          "language": "ko",
          "subject": "math",
          "level": "high_school"
        }
      }
    ]
  },
  "confidence": 0.95,
  "reasoning": "Query clearly specifies Korean language, math subject, and high school level..."
}
```

**Status Codes:**
- `200`: Plan generated successfully
- `400`: Invalid query
- `503`: Planner service unavailable

---

## 📊 Data Models

### Task Status

```typescript
enum TaskStatus {
  PENDING = "PENDING",
  STARTED = "STARTED", 
  SUCCESS = "SUCCESS",
  FAILURE = "FAILURE"
}
```

### Model Configuration

```typescript
interface ModelConfig {
  name: string;
  api_base: string;
  api_key: string;
  model_type: "openai" | "anthropic" | "huggingface" | "custom";
  temperature?: number;
  max_tokens?: number;
  timeout?: number;
}
```

### Evaluation Criteria

```typescript
interface EvaluationCriteria {
  language?: string;
  subject_type?: string;
  task_type?: string;
  difficulty?: string;
  sample_size?: number;
  metrics?: string[];
}
```

### Evaluation Result

```typescript
interface EvaluationResult {
  model_results: ModelResult[];
  evaluation_metadata: EvaluationMetadata;
}

interface ModelResult {
  model_name: string;
  average_score: number;
  accuracy: number;
  total_samples: number;
  execution_time: number;
  detailed_metrics: Record<string, number>;
}
```

## 🚨 Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid model configuration",
    "details": {
      "field": "api_key",
      "issue": "API key is required"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

### Common Error Codes

- `VALIDATION_ERROR`: Request validation failed
- `AUTHENTICATION_ERROR`: Invalid or missing authentication
- `RATE_LIMIT_ERROR`: Too many requests
- `RESOURCE_NOT_FOUND`: Requested resource not found
- `INTERNAL_ERROR`: Internal server error
- `SERVICE_UNAVAILABLE`: External service unavailable

## 🔄 Rate Limiting

API endpoints are rate limited to ensure fair usage:

- **General endpoints**: 100 requests per minute
- **Evaluation endpoints**: 10 requests per minute
- **Health check**: 1000 requests per minute

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248600
```

## 📝 Request/Response Examples

### Complete Evaluation Flow

1. **Submit Evaluation:**
```bash
curl -X POST "http://localhost:8000/api/v1/leaderboard/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare GPT-4 and Claude on math problems",
    "models": [
      {
        "name": "gpt-4",
        "api_base": "https://api.openai.com/v1",
        "api_key": "sk-...",
        "model_type": "openai"
      }
    ]
  }'
```

2. **Check Status:**
```bash
curl "http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000"
```

3. **Browse Results:**
```bash
curl "http://localhost:8000/api/v1/leaderboard/browse?subject_type=Math&limit=10"
```

## 🔧 SDK and Client Libraries

### Python Client Example

```python
import requests

class BenchHubClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        
    def submit_evaluation(self, query, models):
        response = requests.post(
            f"{self.base_url}/api/v1/leaderboard/generate",
            json={"query": query, "models": models}
        )
        return response.json()
    
    def get_task_status(self, task_id):
        response = requests.get(
            f"{self.base_url}/api/v1/tasks/{task_id}"
        )
        return response.json()

# Usage
client = BenchHubClient()
result = client.submit_evaluation(
    "Compare models on math problems",
    [{"name": "gpt-4", "api_key": "sk-...", ...}]
)
```

### JavaScript Client Example

```javascript
class BenchHubClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }
  
  async submitEvaluation(query, models) {
    const response = await fetch(`${this.baseUrl}/api/v1/leaderboard/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, models })
    });
    return response.json();
  }
  
  async getTaskStatus(taskId) {
    const response = await fetch(`${this.baseUrl}/api/v1/tasks/${taskId}`);
    return response.json();
  }
}
```

## 📚 Additional Resources

- **OpenAPI Specification**: Available at `/docs` endpoint
- **Interactive API Explorer**: Available at `/docs` endpoint  
- **Redoc Documentation**: Available at `/redoc` endpoint
- **Postman Collection**: [Download link] (TODO: Add collection)

---

*For questions about the API or to report issues, please visit our [GitHub repository](https://github.com/HAE-RAE/BenchhubPlus) or contact our support team.*