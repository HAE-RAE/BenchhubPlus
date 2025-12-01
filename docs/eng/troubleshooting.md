# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with BenchHub Plus.

## 🚨 Common Issues

### Installation Issues

#### Docker Installation Problems

**Issue**: Docker containers fail to start
```bash
Error: Cannot connect to the Docker daemon
```

**Solutions**:
1. **Check Docker service**:
   ```bash
   sudo systemctl status docker
   sudo systemctl start docker
   ```

2. **Check Docker permissions**:
   ```bash
   sudo usermod -aG docker $USER
   # Log out and back in
   ```

3. **Verify Docker installation**:
   ```bash
   docker --version
   docker-compose --version
   ```

#### Database Connection Issues

**Issue**: PostgreSQL connection failed
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solutions**:
1. **Check PostgreSQL status**:
   ```bash
   # Docker
   docker-compose logs postgres
   
   # Local installation
   sudo systemctl status postgresql
   ```

2. **Verify connection parameters**:
   ```bash
   # Test connection
   psql -h localhost -U benchhub -d benchhub_plus
   ```

3. **Check firewall settings**:
   ```bash
   sudo ufw status
   sudo ufw allow 5432
   ```

#### Redis Connection Issues

**Issue**: Redis connection failed
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solutions**:
1. **Check Redis status**:
   ```bash
   # Docker
   docker-compose logs redis
   
   # Local installation
   sudo systemctl status redis
   ```

2. **Test Redis connection**:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

3. **Check Redis configuration**:
   ```bash
   redis-cli config get bind
   redis-cli config get port
   ```

### Runtime Issues

#### API Endpoint Errors

**Issue**: 500 Internal Server Error
```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Internal server error"
  }
}
```

**Debugging Steps**:
1. **Check backend logs**:
   ```bash
   docker-compose logs backend
   # or
   tail -f logs/backend.log
   ```

2. **Verify environment variables**:
   ```bash
   docker-compose exec backend env | grep -E "(DATABASE_URL|OPENAI_API_KEY)"
   ```

3. **Test database connectivity**:
   ```bash
   docker-compose exec backend python -c "
   from apps.core.db import get_db
   next(get_db())
   print('Database connection OK')
   "
   ```

#### Task Processing Issues

**Issue**: Tasks stuck in PENDING status
```
Task remains in PENDING state indefinitely
```

**Solutions**:
1. **Check Celery worker status**:
   ```bash
   docker-compose logs worker
   celery -A apps.worker.celery_app inspect active
   ```

2. **Verify Redis connection**:
   ```bash
   docker-compose exec worker python -c "
   import redis
   r = redis.Redis(host='redis', port=6379, db=0)
   print(r.ping())
   "
   ```

3. **Restart worker**:
   ```bash
   docker-compose restart worker
   ```

#### Frontend Loading Issues

**Issue**: Streamlit app won't load
```
This site can't be reached
```

**Solutions**:
1. **Check frontend logs**:
   ```bash
   docker-compose logs reflex
   ```

2. **Verify port binding**:
   ```bash
   docker-compose ps
   netstat -tlnp | grep 3000
   ```

3. **Check browser console**:
   - Open browser developer tools
   - Look for JavaScript errors
   - Check network requests

### Performance Issues

#### Slow Evaluation Performance

**Issue**: Evaluations take too long to complete

**Optimization Steps**:
1. **Reduce sample size**:
   - Start with smaller sample sizes (10-50)
   - Gradually increase based on performance

2. **Check model API limits**:
   - Verify API rate limits
   - Monitor API usage
   - Consider using multiple API keys

3. **Optimize worker configuration**:
   ```bash
   # Increase worker concurrency
   celery -A apps.worker.celery_app worker --concurrency=4
   ```

4. **Monitor system resources**:
   ```bash
   docker stats
   htop
   ```

#### Database Performance Issues

**Issue**: Slow database queries

**Solutions**:
1. **Check database indexes**:
   ```sql
   -- Connect to database
   \d+ leaderboard_cache
   
   -- Check for missing indexes
   EXPLAIN ANALYZE SELECT * FROM leaderboard_cache WHERE model_name = 'gpt-4';
   ```

2. **Optimize queries**:
   ```python
   # Use pagination
   query = query.offset(offset).limit(limit)
   
   # Use specific columns
   query = query.with_entities(Model.id, Model.name)
   ```

3. **Database maintenance**:
   ```sql
   VACUUM ANALYZE;
   REINDEX DATABASE benchhub_plus;
   ```

## 🔧 Diagnostic Tools

### Health Check Script

Create a comprehensive health check:

```bash
#!/bin/bash
# health_check.sh

echo "🏥 BenchHub Plus Health Check"
echo "================================"

# Check Docker containers
echo "📦 Docker Containers:"
docker-compose ps

# Check API health
echo -e "\n🌐 API Health:"
curl -s http://localhost:8000/api/v1/health | jq '.'

# Check database
echo -e "\n🗄️  Database:"
docker-compose exec -T postgres pg_isready -U benchhub

# Check Redis
echo -e "\n🔴 Redis:"
docker-compose exec -T redis redis-cli ping

# Check disk space
echo -e "\n💾 Disk Space:"
df -h

# Check memory usage
echo -e "\n🧠 Memory Usage:"
free -h

# Check logs for errors
echo -e "\n📋 Recent Errors:"
docker-compose logs --tail=10 | grep -i error
```

### Log Analysis

```bash
# Analyze logs for common issues
grep -i "error\|exception\|failed" logs/*.log

# Monitor real-time logs
docker-compose logs -f --tail=100

# Filter specific service logs
docker-compose logs backend | grep ERROR
```

### Performance Monitoring

```python
# Add to your application for monitoring
import time
import logging
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logging.info(f"{func.__name__} executed in {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logging.error(f"{func.__name__} failed after {execution_time:.2f}s: {e}")
            raise
    return wrapper
```

## 🐛 Debugging Techniques

### Backend Debugging

1. **Enable debug mode**:
   ```bash
   export DEBUG=true
   export LOG_LEVEL=debug
   ```

2. **Add debug logging**:
   ```python
   import logging
   logger = logging.getLogger(__name__)
   
   logger.debug(f"Processing request: {request}")
   logger.info(f"Task started: {task_id}")
   logger.error(f"Error occurred: {error}")
   ```

3. **Use interactive debugger**:
   ```python
   import pdb; pdb.set_trace()
   # or
   import ipdb; ipdb.set_trace()
   ```

### Frontend Debugging

1. **Reflex debugging**:
   - Run the frontend with verbose logs: `reflex run --env dev --loglevel debug --backend-port 8001 --frontend-port 3000`
   - Add temporary `print()` or `logger.debug()` calls inside `rx.State` methods; they appear in the Reflex backend console.
   - Surface errors to the UI with `rx.toast.error(...)` for quick feedback.

2. **Browser debugging**:
   - Open Developer Tools (F12)
   - Check Console for JavaScript errors
   - Monitor Network tab for API calls (ensure requests hit the FastAPI backend successfully)
   - Verify the WebSocket connection to the Reflex backend stays open

### Worker Debugging

1. **Run worker in debug mode**:
   ```bash
   celery -A apps.worker.celery_app worker --loglevel=debug --concurrency=1
   ```

2. **Monitor task execution**:
   ```bash
   celery -A apps.worker.celery_app events
   ```

3. **Inspect worker state**:
   ```bash
   celery -A apps.worker.celery_app inspect active
   celery -A apps.worker.celery_app inspect scheduled
   celery -A apps.worker.celery_app inspect reserved
   ```

## 🔍 Error Code Reference

### API Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| `VALIDATION_ERROR` | Request validation failed | Check request format and required fields |
| `AUTHENTICATION_ERROR` | Invalid API key | Verify API key configuration |
| `RATE_LIMIT_ERROR` | Too many requests | Reduce request frequency |
| `RESOURCE_NOT_FOUND` | Resource not found | Check resource ID and permissions |
| `INTERNAL_ERROR` | Server error | Check logs and system status |
| `SERVICE_UNAVAILABLE` | External service down | Check external service status |

### Task Error Codes

| Status | Description | Action |
|--------|-------------|--------|
| `PENDING` | Task queued | Wait or check worker status |
| `STARTED` | Task running | Monitor progress |
| `SUCCESS` | Task completed | Review results |
| `FAILURE` | Task failed | Check error message and logs |
| `RETRY` | Task retrying | Wait for completion |
| `REVOKED` | Task cancelled | Task was manually cancelled |

## 🛠️ Recovery Procedures

### Database Recovery

1. **Backup current state**:
   ```bash
   docker-compose exec postgres pg_dump -U benchhub benchhub_plus > backup.sql
   ```

2. **Reset database**:
   ```bash
   docker-compose down
   docker volume rm benchhub_postgres_data
   docker-compose up -d postgres
   ```

3. **Restore from backup**:
   ```bash
   docker-compose exec -T postgres psql -U benchhub benchhub_plus < backup.sql
   ```

### Cache Recovery

1. **Clear Redis cache**:
   ```bash
   docker-compose exec redis redis-cli FLUSHALL
   ```

2. **Restart Redis**:
   ```bash
   docker-compose restart redis
   ```

### Complete System Reset

1. **Stop all services**:
   ```bash
   docker-compose down -v
   ```

2. **Remove all data**:
   ```bash
   docker system prune -a
   docker volume prune
   ```

3. **Redeploy**:
   ```bash
   ./scripts/deploy.sh development
   ```

## 📞 Getting Help

### Before Seeking Help

1. **Check this troubleshooting guide**
2. **Review system logs**
3. **Verify configuration**
4. **Test with minimal setup**
5. **Search existing issues**

### Information to Include

When reporting issues, include:

- **System information**: OS, Docker version, Python version
- **Installation method**: Docker, local, etc.
- **Error messages**: Complete error logs
- **Steps to reproduce**: Detailed reproduction steps
- **Configuration**: Relevant environment variables (redact secrets)
- **Logs**: Recent application logs

### Support Channels

1. **GitHub Issues**: Bug reports and feature requests
2. **GitHub Discussions**: General questions and help
3. **Documentation**: Check all documentation first
4. **Community**: Stack Overflow with `benchhub-plus` tag

### Creating Good Bug Reports

```markdown
## Bug Report

**Environment:**
- OS: Ubuntu 20.04
- Docker: 20.10.8
- Python: 3.11.0

**Steps to Reproduce:**
1. Start application with `./scripts/deploy.sh development`
2. Navigate to evaluation page
3. Submit evaluation with GPT-4 model
4. Error occurs

**Expected Behavior:**
Evaluation should start successfully

**Actual Behavior:**
500 Internal Server Error

**Error Logs:**
```
[ERROR] 2024-01-15 10:30:00 - Model API call failed: Invalid API key
```

**Configuration:**
- OPENAI_API_KEY: sk-... (redacted)
- DATABASE_URL: postgresql://...
```

## 🔄 Maintenance

### Regular Maintenance Tasks

1. **Log rotation**:
   ```bash
   # Setup logrotate
   sudo nano /etc/logrotate.d/benchhub
   ```

2. **Database maintenance**:
   ```sql
   -- Weekly maintenance
   VACUUM ANALYZE;
   
   -- Monthly maintenance
   REINDEX DATABASE benchhub_plus;
   ```

3. **Cache cleanup**:
   ```bash
   # Clear old cache entries
   docker-compose exec redis redis-cli --scan --pattern "cache:*" | xargs docker-compose exec redis redis-cli del
   ```

4. **API-driven cleanup (BenchHub Plus)**:
   ```bash
   # Schedule cleanup (admin only) - defaults: tasks/samples/cache, days_old=7, dry_run=true recommended first
   curl -X POST http://localhost:8001/api/v1/maintenance/cleanup \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <admin_token>" \
     -d '{"dry_run": true, "resources": ["tasks","samples","cache"], "days_old": 7, "limit": 500, "hard_delete": false}'

   # Check status/progress
   curl http://localhost:8001/api/v1/maintenance/cleanup/<task_id> \
     -H "Authorization: Bearer <admin_token>"
   ```
   - `status` returns `PENDING|RUNNING|PARTIAL|SUCCESS|FAILED`, with per-resource `{deleted, skipped, errors, duration_ms}` and `progress{current,total,stage,eta_seconds}`.
   - Use `dry_run=true` to inspect impact before real deletion. Set `hard_delete=true` to physically remove cache rows; otherwise they are quarantined.

4. **Update dependencies**:
   ```bash
   pip list --outdated
   pip install --upgrade package_name
   ```

### Monitoring Setup

1. **System monitoring**:
   ```bash
   # Install monitoring tools
   sudo apt install htop iotop nethogs
   ```

2. **Application monitoring**:
   ```python
   # Add metrics collection
   from prometheus_client import Counter, Histogram
   
   REQUEST_COUNT = Counter('requests_total', 'Total requests')
   REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')
   ```

3. **Log monitoring**:
   ```bash
   # Setup log monitoring
   tail -f logs/*.log | grep -E "(ERROR|CRITICAL)"
   ```

---

*If you can't find a solution to your problem in this guide, please check our [GitHub Issues](https://github.com/HAE-RAE/BenchhubPlus/issues) or create a new issue with detailed information about your problem.*
