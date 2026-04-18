# 🔐 PHASE 2: SECURITY & PERFORMANCE HARDENING
**Timeline: 2-3 weeks | Priority: HIGH | Estimated Effort: 40-60 hours**

---

## 📋 Phase 2 Overview

### What We're Tackling
1. **Security Hardening** (Remaining vulnerabilities)
2. **Performance Optimization** (Speed & efficiency)
3. **Infrastructure** (Monitoring, logging, caching)

### Goals
- ✅ Address remaining security gaps
- ✅ Reduce API latency from 112ms → <80ms (28% faster)
- ✅ Implement caching layer (60% hit rate target)
- ✅ Add compression (70% payload reduction)
- ✅ Set up monitoring and alerting

### Success Metrics
| Metric | Current | Target | Improvement |
|--------|---------|--------|------------|
| API Latency | 112ms | <80ms | ⬇️ 28% |
| Cache Hit Rate | 0% | 60% | ⬆️ 60% |
| Payload Size | 100% | 30% | ⬇️ 70% |
| Error Rate | Unknown | <0.1% | ✅ Monitored |
| Uptime | Unknown | 99.9% | ✅ Tracked |

---

## 🔒 PART 1: ADVANCED SECURITY HARDENING

### 2.1 API Key Management (CRITICAL)
**Status**: Not implemented | **Time**: 2 hours

#### Current Risk
```python
# ❌ CURRENT: Keys in .env (readable by developers)
GEMINI_API_KEY=sk-abc123...
SUPABASE_KEY=service_role_key...
```

#### Solution: Google Secret Manager
**Recommended for**: Production environments

```python
# ✅ NEW: Use Secret Manager
from google.cloud import secretmanager

def get_secret(project_id: str, secret_id: str, version_id: str = "latest") -> str:
    """
    Retrieve secret from Google Secret Manager
    
    Args:
        project_id: GCP project ID
        secret_id: Name of the secret
        version_id: Version (default: latest)
    
    Returns:
        Secret value string
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    
    try:
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Failed to retrieve secret {secret_id}: {e}")
        raise

# Usage at startup
if os.getenv("ENV") == "production":
    GEMINI_API_KEY = get_secret(PROJECT_ID, "gemini-api-key")
    SUPABASE_KEY = get_secret(PROJECT_ID, "supabase-key")
else:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
```

#### Setup Instructions

**Step 1: Create secrets in GCP**
```bash
# Create Gemini API key secret
echo -n "sk-abc123..." | gcloud secrets create gemini-api-key --data-file=-

# Create Supabase key secret
echo -n "your-supabase-key..." | gcloud secrets create supabase-key --data-file=-

# List all secrets
gcloud secrets list
```

**Step 2: Grant permissions**
```bash
# Grant Service Account access to secrets
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

**Step 3: Add to requirements.txt**
```
google-cloud-secret-manager
```

**Step 4: Update main.py**
```python
import os
from google.cloud import secretmanager

# At top of file
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-project")
ENV = os.getenv("ENV", "development")

# Better initialization
def initialize_api_keys():
    """Safely load API keys from Secret Manager or .env"""
    global GEMINI_API_KEY, SUPABASE_KEY
    
    try:
        if ENV == "production":
            GEMINI_API_KEY = get_secret(PROJECT_ID, "gemini-api-key")
            SUPABASE_KEY = get_secret(PROJECT_ID, "supabase-key")
            logger.info("Loaded keys from Secret Manager")
        else:
            GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
            SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            logger.info("Loaded keys from .env (development)")
    except Exception as e:
        logger.error(f"Failed to initialize API keys: {e}")
        raise SystemExit("Cannot start without API keys")

initialize_api_keys()
```

---

### 2.2 Request Size Limits (HIGH)
**Status**: Not implemented | **Time**: 30 min

#### Current Risk
```python
# ❌ CURRENT: No size limits (could receive 100MB files)
@app.post("/generate-feedback")
async def generate_feedback(request: FeedbackRequest): ...
```

#### Solution: Add Request Limits

```python
# ✅ NEW: Enforce size limits
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

app = FastAPI(title="Biomech AI - Hardened Production Backend")

# Set max request body size (10MB)
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10 MB

# Add middleware to check request size
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    """Enforce maximum request size"""
    if request.method in ["POST", "PUT", "PATCH"]:
        # Check content-length header
        if "content-length" in request.headers:
            content_length = int(request.headers["content-length"])
            if content_length > MAX_REQUEST_SIZE:
                logger.warning(f"Request too large: {content_length} bytes")
                return JSONResponse(
                    status_code=413,
                    content={
                        "detail": f"Request body too large. Max: {MAX_REQUEST_SIZE} bytes",
                        "status": "error"
                    }
                )
    
    response = await call_next(request)
    return response

# Also set in Pydantic models
class FeedbackRequest(BaseModel):
    metrics: MetricsData
    exercise_type: str = Field(..., min_length=1, max_length=50)
    user_id: Optional[str] = Field(None, max_length=100)
    
    class Config:
        # Limit JSON input to 1MB
        json_encoders = {}
        max_json_depth = 10  # Prevent deeply nested objects
```

---

### 2.3 HTTPS Enforcement & Security Headers (HIGH)
**Status**: Not implemented | **Time**: 1 hour

#### In Production

```python
# ✅ Add security middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.gzip import GZIPMiddleware

# ✅ Trust only specific hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["yourdomain.com", "www.yourdomain.com"]
)

# ✅ Add security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # Prevent MIME sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Enable XSS protection
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Content Security Policy
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    # HSTS (HTTP Strict Transport Security)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Referrer Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response

# ✅ Enforce HTTPS in production
if ENV == "production":
    from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
    app.add_middleware(HTTPSRedirectMiddleware)
```

---

### 2.4 Database Security (MEDIUM)
**Status**: Partial | **Time**: 1 hour

#### Add Row-Level Security (RLS) in Supabase

```sql
-- ✅ Enable RLS on profiles table
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- ✅ Only users can see their own profile
CREATE POLICY "Users can only view their own profile" ON profiles
  FOR SELECT
  USING (auth.uid() = user_id);

-- ✅ Users can only update their own profile
CREATE POLICY "Users can only update their own profile" ON profiles
  FOR UPDATE
  USING (auth.uid() = user_id);

-- ✅ Service role can access all (for backend)
CREATE POLICY "Service role can access all profiles" ON profiles
  FOR ALL
  USING (current_user_id = 'service_role');
```

#### In Python: Enforce permissions

```python
# ✅ Verify user owns the data they're accessing
async def verify_user_ownership(user_id: str, resource_id: str) -> bool:
    """Check if user owns the resource"""
    try:
        result = supabase.table("profiles").select("id").eq("id", resource_id).eq("user_id", user_id).execute()
        return len(result.data) > 0
    except Exception as e:
        logger.error(f"Ownership check failed: {e}")
        return False

# ✅ Use in endpoint
@app.get("/profile/{profile_id}")
async def get_profile(profile_id: str, user_id: str):
    """Get user profile (with ownership check)"""
    if not await verify_user_ownership(user_id, profile_id):
        logger.warning(f"Unauthorized access attempt: user {user_id} accessing profile {profile_id}")
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = supabase.table("profiles").select("*").eq("id", profile_id).execute()
    return result.data[0] if result.data else None
```

---

## ⚡ PART 2: PERFORMANCE OPTIMIZATION

### 2.5 Caching Layer (HIGH)
**Status**: Not implemented | **Time**: 3 hours

#### Setup Redis

```bash
# Install Redis locally (for development)
# macOS
brew install redis

# Ubuntu/Debian
sudo apt-get install redis-server

# Windows: Use WSL or Docker
docker run -d -p 6379:6379 redis:7-alpine

# Verify connection
redis-cli ping  # Should return PONG
```

#### Add Redis to Backend

```python
# ✅ Install dependency
# pip install redis aioredis

from redis import asyncio as aioredis
from typing import Optional
import pickle

# Initialize Redis client
redis_client: Optional[aioredis.Redis] = None

async def init_redis():
    """Initialize Redis connection at startup"""
    global redis_client
    try:
        redis_client = await aioredis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379"),
            encoding="utf8",
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("Redis connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        redis_client = None

@app.on_event("startup")
async def startup():
    """Initialize services on startup"""
    await init_redis()

@app.on_event("shutdown")
async def shutdown():
    """Close connections on shutdown"""
    if redis_client:
        await redis_client.close()

# ✅ Caching decorator
def cache_key(*args, **kwargs) -> str:
    """Generate cache key from function args"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}:{v}" for k, v in kwargs.items()])
    return "|".join(key_parts)

async def cached_analysis(
    metrics_dict: Dict,
    exercise_type: str,
    ttl: int = 3600  # 1 hour cache
) -> Optional[Dict]:
    """
    Get cached analysis result if available
    
    Args:
        metrics_dict: Biomechanical metrics
        exercise_type: Type of exercise
        ttl: Time-to-live in seconds
    
    Returns:
        Cached result or None
    """
    if not redis_client:
        return None
    
    try:
        # Create cache key from metrics
        key = f"analysis:{hash(str(metrics_dict))}:{exercise_type}"
        
        # Try to get from cache
        cached = await redis_client.get(key)
        if cached:
            logger.debug(f"Cache hit: {key}")
            return json.loads(cached)
        
        logger.debug(f"Cache miss: {key}")
        return None
    except Exception as e:
        logger.warning(f"Cache read error: {e}")
        return None

async def cache_analysis(
    metrics_dict: Dict,
    exercise_type: str,
    result: Dict,
    ttl: int = 3600
) -> None:
    """Store analysis result in cache"""
    if not redis_client:
        return
    
    try:
        key = f"analysis:{hash(str(metrics_dict))}:{exercise_type}"
        await redis_client.setex(key, ttl, json.dumps(result))
        logger.debug(f"Cached result: {key}")
    except Exception as e:
        logger.warning(f"Cache write error: {e}")

# ✅ Use in endpoint
@app.post("/generate-feedback", response_model=AnalysisResponse)
@limiter.limit("10/minute")
async def generate_feedback(request: Request, payload: FeedbackRequest) -> AnalysisResponse:
    """Generate feedback with caching"""
    start_time = time.time()
    metrics_dict = payload.metrics.dict()
    exercise_type = payload.exercise_type
    user_id = payload.user_id
    
    logger.info(f"Feedback request: exercise={exercise_type}, user={user_id}")
    
    # Layer 0: Check cache
    cached_result = await cached_analysis(metrics_dict, exercise_type)
    if cached_result:
        logger.info(f"Returning cached result for {exercise_type}")
        return AnalysisResponse(**cached_result)
    
    # Layers 1-4: Normal processing
    risk_info = {"risk_level": "UNKNOWN", "risk_factors": []}
    try:
        risk_info = analyze_injury_risk(metrics_dict)
    except Exception as e:
        logger.error(f"Risk analysis error: {e}", exc_info=True)
    
    # ... rest of processing ...
    
    # Cache the result
    await cache_analysis(metrics_dict, exercise_type, report.dict())
    
    return report
```

#### Configure Redis in `.env`

```
# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_TTL=3600  # 1 hour
CACHE_ENABLED=true
```

---

### 2.6 Async Processing (HIGH)
**Status**: Partially implemented | **Time**: 2 hours

#### Current Issue
```python
# ❌ CURRENT: Gemini API calls block response
response = model.generate_content(prompt, request_options={"timeout": 10})
```

#### Solution: Background Tasks

```python
# ✅ NEW: Use background tasks for slow operations
from celery import Celery
from typing import Any

# Option 1: FastAPI BackgroundTasks (simple, no external service)
from fastapi import BackgroundTasks

@app.post("/analyze-video-async")
async def analyze_video_async(
    file: UploadFile,
    background_tasks: BackgroundTasks
):
    """Upload video for processing"""
    task_id = str(uuid.uuid4())
    
    # Add background task
    background_tasks.add_task(process_video_background, task_id, file)
    
    logger.info(f"Video processing queued: {task_id}")
    return {
        "status": "queued",
        "task_id": task_id,
        "message": "Video processing started. Check status with /analysis/{task_id}"
    }

async def process_video_background(task_id: str, file: UploadFile):
    """Process video in background"""
    try:
        logger.info(f"Processing video: {task_id}")
        
        # Store task status
        if redis_client:
            await redis_client.set(
                f"task:{task_id}",
                json.dumps({
                    "status": "processing",
                    "progress": 0,
                    "created_at": time.time()
                }),
                ex=86400  # 24 hour TTL
            )
        
        # Process video (slow operation)
        result = await _process_video_intensive(file)
        
        # Store result
        if redis_client:
            await redis_client.set(
                f"task:{task_id}",
                json.dumps({
                    "status": "completed",
                    "result": result,
                    "completed_at": time.time()
                }),
                ex=3600  # 1 hour TTL after completion
            )
        
        logger.info(f"Video processing completed: {task_id}")
    except Exception as e:
        logger.error(f"Video processing failed: {task_id}: {e}", exc_info=True)
        if redis_client:
            await redis_client.set(
                f"task:{task_id}",
                json.dumps({
                    "status": "failed",
                    "error": str(e)
                }),
                ex=3600
            )

@app.get("/analysis/{task_id}")
async def get_analysis_status(task_id: str):
    """Check async task status"""
    if not redis_client:
        return {"status": "error", "message": "Redis not available"}
    
    try:
        task_data = await redis_client.get(f"task:{task_id}")
        if not task_data:
            return {"status": "error", "message": "Task not found"}
        
        return json.loads(task_data)
    except Exception as e:
        logger.error(f"Status check failed: {task_id}: {e}")
        return {"status": "error", "message": "Failed to retrieve status"}

async def _process_video_intensive(file: UploadFile) -> Dict[str, Any]:
    """Intensive video processing (can take time)"""
    # Save file temporarily
    temp_path = f"/tmp/{uuid.uuid4()}.mp4"
    
    try:
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process frames
        results = []
        cap = cv2.VideoCapture(temp_path)
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Analyze each frame
            keypoints, _ = engine.process_frame(frame)
            if keypoints:
                analysis = get_biomechanical_analysis(keypoints)
                results.append(analysis)
        
        cap.release()
        return {
            "frames_processed": len(results),
            "average_risk": sum([r.get("risk_level") for r in results]) / len(results) if results else 0
        }
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)
```

---

### 2.7 Response Compression (MEDIUM)
**Status**: Not implemented | **Time**: 15 min

#### Add GZIP Compression

```python
# ✅ Already added in imports, but configure it
from fastapi.middleware.gzip import GZIPMiddleware

# Add after CORS middleware
app.add_middleware(GZIPMiddleware, minimum_size=1000)  # Compress responses > 1KB

# Verify in response headers
# Client should see: Content-Encoding: gzip
```

---

### 2.8 Database Query Optimization (HIGH)
**Status**: Not implemented | **Time**: 2 hours

#### Current Issues
```python
# ❌ CURRENT: No indexes, O(n) queries
result = supabase.table("sessions").select("*").eq("user_id", user_id).execute()
```

#### Add Database Indexes

```sql
-- ✅ Create indexes for common queries
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_exercise_type ON sessions(exercise);
CREATE INDEX idx_sessions_created_at ON sessions(created_at DESC);
CREATE INDEX idx_profiles_email ON profiles(email);
CREATE INDEX idx_ai_analysis_user_id ON ai_analysis_reports(user_id);

-- ✅ Create composite index for common joins
CREATE INDEX idx_sessions_user_exercise ON sessions(user_id, exercise);

-- Verify indexes
SELECT * FROM pg_stat_user_indexes WHERE schemaname = 'public';
```

#### Optimize Python Queries

```python
# ✅ Use select() instead of select("*")
@app.get("/user-sessions/{user_id}")
async def get_user_sessions(user_id: str, limit: int = 100):
    """Get recent sessions for user (optimized)"""
    try:
        # Only fetch needed fields
        result = supabase.table("sessions").select(
            "id, exercise, reps, score, duration, created_at"
        ).eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
        
        return result.data
    except Exception as e:
        logger.error(f"Session query failed: {e}")
        raise HTTPException(status_code=500, detail="Query failed")

# ✅ Add pagination for large datasets
@app.get("/sessions")
async def list_sessions(
    offset: int = 0,
    limit: int = 50,
    exercise: Optional[str] = None
):
    """List sessions with pagination"""
    query = supabase.table("sessions").select("*")
    
    if exercise:
        query = query.eq("exercise", exercise)
    
    result = query.order("created_at", desc=True).range(offset, offset + limit).execute()
    
    return {
        "data": result.data,
        "offset": offset,
        "limit": limit,
        "has_more": len(result.data) == limit
    }
```

---

## 📊 PART 3: MONITORING & OBSERVABILITY

### 2.9 Error Tracking (HIGH)
**Status**: Not implemented | **Time**: 1 hour

#### Add Sentry Integration

```python
# ✅ Install Sentry SDK
# pip install sentry-sdk

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

# Initialize Sentry
if ENV == "production":
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,  # Sample 10% of transactions
        environment=ENV,
        attach_stacktrace=True
    )
    logger.info("Sentry initialized")
```

#### Configure in `.env`

```
# Sentry Configuration
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

### 2.10 Performance Metrics (HIGH)
**Status**: Not implemented | **Time**: 2 hours

#### Add Prometheus Metrics

```python
# ✅ Install dependencies
# pip install prometheus-client

from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time

# Define metrics
api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0)
)

cache_hits = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['operation']
)

cache_misses = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['operation']
)

# Add metrics middleware
@app.middleware("http")
async def add_metrics_middleware(request: Request, call_next):
    """Track request metrics"""
    start_time = time.time()
    
    response = await call_next(request)
    
    # Record metrics
    duration = time.time() - start_time
    api_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    api_request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    response.headers["X-Process-Time"] = str(duration)
    
    return response

# Expose metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")

# Track cache operations
async def cached_analysis(...) -> Optional[Dict]:
    if not redis_client:
        return None
    
    try:
        key = f"analysis:{hash(str(metrics_dict))}:{exercise_type}"
        cached = await redis_client.get(key)
        if cached:
            cache_hits.labels(operation="analysis").inc()
            return json.loads(cached)
        
        cache_misses.labels(operation="analysis").inc()
        return None
    except Exception as e:
        logger.warning(f"Cache error: {e}")
        return None
```

#### View Metrics

```bash
# Access raw metrics
curl http://localhost:8000/metrics

# Expected output:
# # HELP api_requests_total Total API requests
# # TYPE api_requests_total counter
# api_requests_total{endpoint="/generate-feedback",method="POST",status="200"} 125.0
# ...
```

---

## 📋 Phase 2 Implementation Checklist

### Week 1: Security Hardening

- [ ] **2.1 API Key Management** (2 hrs)
  - [ ] Set up Google Secret Manager
  - [ ] Create secrets for API keys
  - [ ] Update code to use Secret Manager
  - [ ] Test in development and production

- [ ] **2.2 Request Size Limits** (30 min)
  - [ ] Add middleware to check content-length
  - [ ] Set MAX_REQUEST_SIZE constant
  - [ ] Test with oversized requests

- [ ] **2.3 Security Headers** (1 hr)
  - [ ] Add TrustedHostMiddleware
  - [ ] Add security headers middleware
  - [ ] Test with browser dev tools
  - [ ] Verify HSTS, CSP, X-Frame-Options

- [ ] **2.4 Database Security** (1 hr)
  - [ ] Enable RLS on all tables
  - [ ] Create security policies
  - [ ] Test row-level access control

### Week 2: Performance Optimization

- [ ] **2.5 Caching Layer** (3 hrs)
  - [ ] Install and configure Redis
  - [ ] Implement cache_key() function
  - [ ] Add cached_analysis() decorator
  - [ ] Update /generate-feedback to use cache
  - [ ] Monitor cache hit rate

- [ ] **2.6 Async Processing** (2 hrs)
  - [ ] Create background task handlers
  - [ ] Add /analyze-video-async endpoint
  - [ ] Add /analysis/{task_id} status endpoint
  - [ ] Test with large files

- [ ] **2.7 Response Compression** (15 min)
  - [ ] Configure GZIPMiddleware
  - [ ] Test with curl (Accept-Encoding: gzip)
  - [ ] Verify 70% payload reduction

- [ ] **2.8 Database Optimization** (2 hrs)
  - [ ] Create indexes on all foreign keys
  - [ ] Analyze query plans
  - [ ] Optimize slow queries
  - [ ] Profile queries with EXPLAIN

### Week 3: Monitoring & Testing

- [ ] **2.9 Error Tracking** (1 hr)
  - [ ] Set up Sentry account
  - [ ] Initialize Sentry SDK
  - [ ] Test error reporting
  - [ ] Configure alerts

- [ ] **2.10 Performance Metrics** (2 hrs)
  - [ ] Add Prometheus client
  - [ ] Define key metrics
  - [ ] Add metrics middleware
  - [ ] Test /metrics endpoint
  - [ ] Set up Grafana dashboard

- [ ] **Testing** (3 hrs)
  - [ ] Create performance benchmarks
  - [ ] Load testing with artillery
  - [ ] Security testing
  - [ ] Cache effectiveness testing

---

## 🚀 Quick Start: Next Actions

### Option 1: Start with Security (Safer Path)
1. Implement 2.1-2.4 first (security hardening)
2. Deploy to staging
3. Then add 2.5-2.8 (performance)

### Option 2: Start with Performance (If Budget Allows)
1. Implement 2.5-2.8 (performance optimization)
2. Quick benchmark improvements
3. Then add 2.1-2.4 (security)

### Option 3: Recommended Balanced Approach
**Week 1**: 2.1, 2.2, 2.3 (security - highest ROI)
**Week 2**: 2.5 (caching - biggest performance impact)
**Week 2**: 2.6, 2.7 (async + compression)
**Week 3**: 2.8, 2.9, 2.10 (optimization + monitoring)

---

## 📦 Dependencies for Phase 2

Add to `requirements.txt`:

```
# Security
google-cloud-secret-manager

# Caching
redis
aioredis

# Compression (already in FastAPI)
# gzip built-in

# Monitoring
sentry-sdk[fastapi]
prometheus-client

# Optional: Async job processing
celery
redis  # backing store
```

---

## 🧪 Success Criteria for Phase 2

After completing Phase 2, you should see:

✅ **Security Score**: 8.5/10 → 9.5/10  
✅ **API Latency**: 112ms → <80ms (28% improvement)  
✅ **Cache Hit Rate**: 0% → 60%  
✅ **Payload Size**: 100% → 30% (70% reduction)  
✅ **Error Visibility**: Errors logged in Sentry  
✅ **Performance Tracked**: Metrics in Prometheus  

---

## 📚 Files to Create/Modify for Phase 2

```
✅ backend/main.py          - Add security headers, metrics, caching
✅ backend/cache.py         - New: Caching utilities
✅ backend/async_tasks.py   - New: Background task handlers
✅ backend/security.py      - New: Security utilities
✅ backend/metrics.py       - New: Prometheus metrics
✅ backend/requirements.txt  - Add new dependencies
✅ .env.example             - Add new config variables
✅ docker-compose.yml       - New: Redis + monitoring stack
```

---

## 🎯 Next Step

Ready to start Phase 2? Choose your focus area:

1. **Start with 2.1-2.4** (Security hardening - 4.5 hours)
2. **Start with 2.5** (Caching - 3 hours, biggest performance win)
3. **Start with infrastructure** (setup Redis, Sentry, Prometheus)

What would you like to implement first?
