# 📚 Biomech AI - API Documentation (Phase 4)

**Version**: 2.0.0-complete  
**Status**: Production-Ready  
**Last Updated**: April 2026

---

## Overview

The Biomech AI API provides real-time biomechanical analysis, AI-powered coaching feedback, and comprehensive exercise tracking with enterprise-grade security, performance optimization, and monitoring.

**Base URL**: `https://api.biomech-ai.com/v2`  
**Authentication**: API Key (X-API-Key header) or JWT Token

---

## Quick Start

### 1. Get API Key

```bash
# Generate API key (requires authentication)
curl -X POST https://api.biomech-ai.com/v2/admin/generate-key \
  -H "Content-Type: application/json" \
  -d '{"name": "My App", "permissions": ["read", "write"]}'
```

### 2. Make First Request

```bash
curl -X GET https://api.biomech-ai.com/v2/health \
  -H "X-API-Key: your_api_key_here"
```

### 3. Analyze Exercise Form

```bash
curl -X POST https://api.biomech-ai.com/v2/generate-feedback \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "metrics": {
      "angles": {"knee": 85.3, "hip": 92.1},
      "deviations": {"knee": 5.2, "hip": 2.1},
      "pose_confidence": 0.95
    },
    "exercise_type": "squat",
    "user_id": "user-123"
  }'
```

---

## API Endpoints

### Health & Status

#### GET `/health`
**Description**: Check API health and service status  
**Rate Limit**: Unlimited  
**Response**: ✅ 200 OK

```json
{
  "status": "healthy",
  "timestamp": "2026-04-17T10:30:00Z",
  "version": "2.0.0-complete",
  "services": {
    "supabase": "connected",
    "gemini": "connected",
    "redis": "connected",
    "pose_engine": "ready"
  }
}
```

#### GET `/metrics`
**Description**: Prometheus metrics for monitoring  
**Rate Limit**: Unlimited  
**Response**: Prometheus text format

#### GET `/cache-stats`
**Description**: Cache performance statistics  
**Rate Limit**: 5/minute  
**Response**: Cache metrics

```json
{
  "redis_enabled": true,
  "redis_used_memory": "256MB",
  "redis_keys": 1240,
  "in_memory_entries": 0
}
```

---

### Analysis Endpoints

#### POST `/generate-feedback`
**Description**: Generate AI coaching feedback for exercise form  
**Rate Limit**: 10/minute per IP  
**Authentication**: Required (API Key or JWT)

**Request Body**:
```json
{
  "metrics": {
    "angles": {
      "knee": { float, 0-180 },
      "hip": { float, 0-180 },
      "ankle": { float, 0-180 },
      "elbow": { float, 0-180 }
    },
    "deviations": {
      "knee": { float },
      "hip": { float },
      "ankle": { float },
      "elbow": { float }
    },
    "pose_confidence": { float, 0-1 },
    "ideal_ranges": {
      "knee": { "min": 80, "max": 90 },
      "hip": { "min": 85, "max": 95 }
    }
  },
  "exercise_type": "squat|pushup|lunge|deadlift|bicep_curl|shoulder_press|plank|general|jog|sprint",
  "user_id": "string (optional)",
  "session_id": "string (optional)"
}
```

**Response** (✅ 200 OK):
```json
{
  "status": "completed|cached",
  "timestamp": 1713359400.123,
  "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "summary": {
    "angles": { "knee": 85.3, "hip": 92.1 },
    "deviations": { "knee": 5.2, "hip": 2.1 },
    "risk": {
      "risk_level": "LOW|MEDIUM|HIGH",
      "risk_score": 28.5,
      "risk_reason": "Slight knee valgus detected",
      "pose_confidence": 0.95
    },
    "pose_confidence": 0.95
  },
  "coach_feedback": {
    "issue": "Slight knee valgus in descent",
    "reason": "Knee angles deviate 5.2° from ideal range",
    "fix": "Focus on keeping knees aligned with toes. Practice with mirror feedback.",
    "confidence": 0.96
  },
  "performance_metrics": {
    "processing_time_sec": 0.842,
    "engine_status": "AI_AUGMENTED|FALLBACK|SAFE_MODE",
    "accuracy": "96.4%|85.0%",
    "source": "cache|live_analysis"
  }
}
```

**Error Responses**:
- 🔴 400 Bad Request: Invalid metrics data
- 🔴 422 Unprocessable Entity: Validation error
- 🔴 429 Too Many Requests: Rate limit exceeded
- 🔴 500 Internal Server Error: Server error

---

### User Data Endpoints

#### POST `/sync-profile`
**Description**: Sync user profile data  
**Rate Limit**: 20/minute  
**Authentication**: Required

**Request Body**:
```json
{
  "id": "user-123",
  "name": "John Done",
  "email": "john@example.com",
  "picture": "https://example.com/profile.jpg",
  "stats": {
    "total_workouts": 42,
    "total_time_minutes": 3600,
    "personal_records": {
      "squat": 225,
      "deadlift": 315
    }
  }
}
```

**Response** (✅ 200 OK):
```json
{
  "status": "success"
}
```

#### POST `/sync-session`
**Description**: Save workout session data  
**Rate Limit**: 20/minute  
**Authentication**: Required

**Request Body**:
```json
{
  "user_id": "user-123",
  "exercise": "squat",
  "reps": 20,
  "score": 87.5,
  "duration": 45.3
}
```

**Response** (✅ 200 OK):
```json
{
  "status": "success"
}
```

---

### Background Tasks (Phase 2.6)

#### POST `/submit-task/{operation}`
**Description**: Submit background task  
**Rate Limit**: 5/minute  
**Operations**: `video_analysis`, `report_generation`, `data_export`

**Response** (✅ 202 Accepted):
```json
{
  "task_id": "task-550e8400-e29b-41d4-a716-446655440000",
  "status": "submitted"
}
```

#### GET `/task/{task_id}`
**Description**: Get background task status  
**Rate Limit**: Unlimited

**Response**:
```json
{
  "task_id": "task-550e8400-e29b-41d4-a716-446655440000",
  "operation": "video_analysis",
  "status": "processing|completed|failed|pending",
  "created_at": "2026-04-17T10:00:00Z",
  "started_at": "2026-04-17T10:00:05Z",
  "progress": 45,
  "result": {}
}
```

---

## Authentication

### API Key Authentication
Include your API key in the `X-API-Key` header:

```bash
curl -X GET https://api.biomech-ai.com/v2/generate-feedback \
  -H "X-API-Key: key_1a2b3c4d5e6f7g8h"
```

### JWT Token Authentication
Include JWT token in the `Authorization` header:

```bash
curl -X GET https://api.biomech-ai.com/v2/generate-feedback \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### Generate API Key
```python
from security import APIKeyManager

key_id, key_token = APIKeyManager.generate_key(
    name="My Application",
    permissions=["read", "write"]
)
print(f"Save this token securely: {key_token}")
```

---

## Error Handling

### Error Response Format
```json
{
  "detail": "Error description",
  "status": "error",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2026-04-17T10:30:00Z"
}
```

### Common Error Codes
| Code | Status | Description |
|------|--------|-------------|
| MISSING_METRICS | 422 | Metrics field is required |
| INVALID_CONFIDENCE | 422 | Pose confidence must be 0-1 |
| UNKNOWN_EXERCISE | 400 | Exercise type not recognized |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |
| SERVER_ERROR | 500 | Internal server error |

---

## Rate Limiting

**Limits by Endpoint**:
| Endpoint | Limit | Period |
|----------|-------|--------|
| `/generate-feedback` | 10 | 1 minute |
| `/sync-profile` | 20 | 1 minute |
| `/sync-session` | 20 | 1 minute |
| `/submit-task` | 5 | 1 minute |
| `/health` | Unlimited | |

**Rate Limit Headers**:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1713359460
```

---

## Performance Optimization

### Caching
- Repeated identical analyses are cached (300 second TTL)
- Cache key: `feedback:{user_id}:{exercise_type}`
- Cache status in response: `"source": "cache"` vs `"source": "live_analysis"`

### Compression
- Responses > 1KB automatically compressed with GZIP
- Include `Accept-Encoding: gzip` header for compression

### Async Processing
- Large video analysis automatically processed in background
- Submit with `/submit-task/video_analysis`
- Check status with `/task/{task_id}`

---

## Best Practices

### 1. Always include User ID
```json
{
  "user_id": "consistent-user-identifier",
  "metrics": { ... }
}
```

### 2. Handle Rate Limits
```python
import time
from typing import Dict

def call_with_retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = int(e.retry_after)  # From header
                time.sleep(wait_time)
            else:
                raise
```

### 3. Cache Results Locally
```python
cache.set(f"analysis:{user_id}", result, ttl=300)
```

### 4. Implement Error Handling
```python
try:
    response = client.post("/generate-feedback", json=data)
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 429:
        # Implement exponential backoff
    elif e.response.status_code >= 500:
        # Retry with backoff
```

### 5. Monitor Metrics
- Check `/metrics` endpoint regularly
- Set up alerts for high error rates
- Track `biomech_analysis_duration_seconds`

---

## Code Examples

### Python
```python
import requests
import time

API_KEY = "your_api_key_here"
BASE_URL = "https://api.biomech-ai.com/v2"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Analyze exercise
payload = {
    "metrics": {
        "angles": {"knee": 85.3, "hip": 92.1},
        "deviations": {"knee": 5.2, "hip": 2.1},
        "pose_confidence": 0.95
    },
    "exercise_type": "squat",
    "user_id": "user-123"
}

response = requests.post(
    f"{BASE_URL}/generate-feedback",
    json=payload,
    headers=headers
)

if response.status_code == 200:
    result = response.json()
    print(f"Analysis ID: {result['analysis_id']}")
    print(f"Issue: {result['coach_feedback']['issue']}")
    print(f"Fix: {result['coach_feedback']['fix']}")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

### JavaScript/TypeScript
```typescript
const API_KEY = 'your_api_key_here';
const BASE_URL = 'https://api.biomech-ai.com/v2';

async function analyzeFeedback(metrics: MetricsData, exercise: string, userId: string) {
  try {
    const response = await fetch(`${BASE_URL}/generate-feedback`, {
      method: 'POST',
      headers: {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        metrics,
        exercise_type: exercise,
        user_id: userId
      })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const result = await response.json();
    return result.coach_feedback;
  } catch (error) {
    console.error('Feedback analysis failed:', error);
    throw error;
  }
}
```

### cURL Examples

**Get Health Status**:
```bash
curl -X GET https://api.biomech-ai.com/v2/health \
  -H "X-API-Key: your_api_key_here"
```

**Submit Analysis**:
```bash
curl -X POST https://api.biomech-ai.com/v2/generate-feedback \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d @request.json
```

---

## Support & Resources

- **Documentation**: https://docs.biomech-ai.com
- **Status Page**: https://status.biomech-ai.com
- **Support Email**: support@biomech-ai.com
- **GitHub Issues**: https://github.com/biomech-ai/api/issues
- **Community**: https://community.biomech-ai.com

---

**Last Updated**: April 2026  
**API Version**: 2.0.0-complete  
**Status**: Production-Ready ✅
