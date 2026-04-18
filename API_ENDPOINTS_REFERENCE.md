# 📡 API Endpoints Reference

**Server**: http://localhost:8000  
**Status**: 🟢 RUNNING  
**API Version**: 2.0.0-complete

---

## 🔗 Available Endpoints

### Health & Status

#### GET `/health`
**Status**: ✅ OPERATIONAL

Check application health and service status.

```bash
curl http://localhost:8000/health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2026-04-17T20:24:16.675773",
  "version": "2.0.0-complete",
  "services": {
    "supabase": "connected",
    "gemini": "connected",
    "redis": "in-memory",
    "pose_engine": "ready"
  }
}
```

---

### Metrics & Monitoring

#### GET `/metrics`
**Status**: ✅ OPERATIONAL

Get Prometheus metrics for monitoring.

```bash
curl http://localhost:8000/metrics
```

**Returns**: Prometheus text format with 50+ metrics

---

### Documentation

#### GET `/docs`
**Status**: ✅ OPERATIONAL

Interactive Swagger UI documentation.

```
http://localhost:8000/docs
```

**Features**:
- Try it out feature
- Request/response schemas
- Authentication examples
- Rate limit information

#### GET `/redoc`
**Status**: ✅ OPERATIONAL

ReDoc API documentation (alternative view).

```
http://localhost:8000/redoc
```

---

## 📋 Phase 2-5 Endpoints (Ready to Use)

### Analysis Endpoints

#### POST `/generate-feedback`
**Authentication**: API Key required  
**Rate Limit**: 10/minute per IP

Generate AI coaching feedback from biomechanical analysis.

**Request Body**:
```json
{
  "metrics": {
    "angles": {"knee": 85.3, "hip": 92.1},
    "deviations": {"knee": 5.2, "hip": 2.1},
    "pose_confidence": 0.95
  },
  "exercise_type": "squat",
  "user_id": "user123",
  "session_id": "session456"
}
```

**Response**:
```json
{
  "status": "success",
  "timestamp": 1713395056.675773,
  "analysis_id": "analysis_abc123",
  "summary": {...},
  "coach_feedback": {
    "issue": "Knee valgus detected",
    "reason": "Knee angle 85.3° indicates inward collapse",
    "fix": "Focus on pushing knees outward, engage glute muscles",
    "confidence": 0.95
  },
  "performance_metrics": {...}
}
```

---

### User Data Endpoints

#### POST `/sync-profile`
**Authentication**: API Key required  
**Rate Limit**: 10/minute per IP

Sync user profile data.

**Request Body**:
```json
{
  "id": "user123",
  "name": "John Athlete",
  "email": "john@example.com",
  "picture": "https://...",
  "stats": {"total_sessions": 42}
}
```

#### POST `/sync-session`
**Authentication**: API Key required  
**Rate Limit**: 10/minute per IP

Sync workout session data.

**Request Body**:
```json
{
  "id": "session456",
  "user_id": "user123",
  "exercise": "squat",
  "reps": 10,
  "performance_score": 8.5
}
```

---

### Background Tasks (Phase 2.6)

#### POST `/submit-task/{operation}`
**Authentication**: API Key required  
**Rate Limit**: 10/minute per IP

Submit background task for processing.

**Path Parameters**:
- `operation`: video_analysis | report_generation | data_export

**Request Body**:
```json
{
  "data": {
    "video_id": "video123",
    "user_id": "user456"
  },
  "priority": 5
}
```

**Response**:
```json
{
  "task_id": "task_abc123",
  "status": "pending",
  "operation": "video_analysis"
}
```

#### GET `/task/{task_id}`
**Authentication**: API Key required

Get background task status.

**Response**:
```json
{
  "task_id": "task_abc123",
  "operation": "video_analysis",
  "status": "processing",
  "progress": 45,
  "created_at": "2026-04-17T20:10:00"
}
```

---

### Utility Endpoints

#### GET `/cache-stats`
**Authentication**: Optional (API Key recommended)

Get cache statistics.

**Response**:
```json
{
  "redis_enabled": false,
  "in_memory_entries": 12,
  "cache_size_mb": 2.3
}
```

#### POST `/clear-cache`
**Authentication**: API Key required (Admin)

Clear all cached data.

**Response**:
```json
{
  "status": "success",
  "cleared": 42,
  "message": "Cache cleared successfully"
}
```

---

## 🔐 Authentication

### API Key Authentication
Include in header:
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/health
```

### JWT Token
Include in header:
```bash
curl -H "Authorization: Bearer your-jwt-token" http://localhost:8000/health
```

---

## ⚙️ Rate Limiting

**Default Limit**: 10 requests per minute per IP

**Headers**:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 9
X-RateLimit-Reset: 1713395116
```

**Over Limit Response** (429):
```json
{
  "detail": "Rate limit exceeded. Try again later.",
  "status": "error",
  "retry_after": 60
}
```

---

## 📊 Response Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | GET /health |
| 201 | Created | POST /sync-profile |
| 400 | Bad Request | Invalid metrics format |
| 401 | Unauthorized | Missing API Key |
| 429 | Rate Limited | Too many requests |
| 500 | Server Error | See logs for details |

---

## 🧪 Test Requests

### Testing with curl

**Health Check**:
```bash
curl http://localhost:8000/health
```

**Metrics**:
```bash
curl http://localhost:8000/metrics
```

**With API Key** (when configured):
```bash
curl -H "X-API-Key: your-key" http://localhost:8000/health
```

**POST Request**:
```bash
curl -X POST http://localhost:8000/sync-profile \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "id": "user123",
    "name": "Test User",
    "email": "test@example.com"
  }'
```

### Testing with Python

```python
import requests

# Health check
response = requests.get('http://localhost:8000/health')
print(response.json())

# With API key
headers = {'X-API-Key': 'your-api-key'}
response = requests.get('http://localhost:8000/health', headers=headers)
print(response.json())

# POST request
data = {
    'metrics': {
        'angles': {'knee': 85},
        'deviations': {'knee': 5},
        'pose_confidence': 0.9
    },
    'exercise_type': 'squat',
    'user_id': 'user123'
}
response = requests.post(
    'http://localhost:8000/generate-feedback',
    json=data,
    headers=headers
)
print(response.json())
```

### Testing with cURL (Extended)

```bash
# Create variables
API_KEY="your-api-key"
BASE_URL="http://localhost:8000"

# Test health
curl -s $BASE_URL/health | jq .

# Get metrics
curl -s $BASE_URL/metrics | head -20

# Generate feedback
curl -X POST $BASE_URL/generate-feedback \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "metrics": {
      "angles": {"knee": 85},
      "deviations": {"knee": 5},
      "pose_confidence": 0.9
    },
    "exercise_type": "squat"
  }' | jq .
```

---

## 🔧 Configuration via Environment

Set these in `.env`:

```env
# API Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5000
LOG_LEVEL=INFO
ENVIRONMENT=development

# Rate Limiting
RATE_LIMIT=10

# Security
API_KEY_SECRET=your-secret-key
JWT_SECRET=your-jwt-secret

# Services
REDIS_URL=redis://localhost:6379
SENTRY_DSN=your-sentry-dsn
```

---

## 🎯 Common Use Cases

### Monitor Application Health
```bash
watch -n 5 'curl -s http://localhost:8000/health | jq .status'
```

### Get All Metrics
```bash
curl http://localhost:8000/metrics | grep biomech
```

### Generate Analysis Feedback
```bash
# See "Testing with Python" example above
```

### Background Job Processing
```bash
# Submit job
JOB_ID=$(curl -X POST http://localhost:8000/submit-task/video_analysis \
  -d '{"data":{"video_id":"v123"}}' | jq -r '.task_id')

# Monitor job
curl http://localhost:8000/task/$JOB_ID
```

---

## 📚 Additional Resources

- [Full API Documentation](API_DOCUMENTATION.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Integration Fixes](INTEGRATION_FIXES_APPLIED.md)
- Interactive Docs: http://localhost:8000/docs

---

## ✨ Status

All endpoints are:
- ✅ Implemented
- ✅ Tested
- ✅ Documented
- ✅ Production-ready

Ready to use immediately!

---

*Last Updated*: April 17, 2026  
*Server Status*: 🟢 RUNNING  
*API Version*: 2.0.0-complete
