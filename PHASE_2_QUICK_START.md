# 🚀 PHASE 2 QUICK START GUIDE

**Estimated Time to Complete**: 15-20 hours  
**Priority Path**: Security → Performance → Monitoring  
**Recommended Team Size**: 1-2 developers

---

## 📋 Choose Your Phase 2 Path

### 🔴 Path A: Security First (Recommended for Production)
**Time: ~6 hours | Risk: Low | Impact: High**

Focus: Protect your data and API

```
Week 1 (Day 1-2):
- 2.1 API Key Management              2 hours
- 2.2 Request Size Limits             30 min
- 2.3 Security Headers                1 hour
- 2.4 Database Security               1 hour
────────────────────────────────────
Total: 4.5 hours

Week 1 (Day 3-5):
- Testing & Verification              1.5 hours
- Deploy to Staging                   Continuous
- Security audit checklist            1 hour
────────────────────────────────────
Total: 6 hours complete
```

### ⚡ Path B: Performance First (Recommended for Speed)
**Time: ~8 hours | Risk: Low | Impact: Very High**

Focus: Make your API faster

```
Week 2 (Day 1-2):
- 2.5 Redis Caching                   3 hours
  (28% latency improvement expected)
- 2.7 Response Compression            15 min
- 2.6 Async Processing               2 hours
────────────────────────────────────
Total: 5.25 hours

Week 2 (Day 3-5):
- 2.8 Database Optimization           2 hours
- Performance Testing                 1 hour
- Benchmark improvements              1 hour
────────────────────────────────────
Total: 8-9 hours complete
```

### ⚖️ Path C: Balanced Approach (Recommended Overall)
**Time: ~12 hours | Risk: Medium | Impact: Maximum**

Focus: Security AND Performance

```
Week 1 (Days 1-2):  Security Hardening
- 2.1, 2.2, 2.3                      2.5 hours

Week 2 (Day 1-2):   Performance Foundation  
- 2.5 Redis Setup                     2 hours
- 2.7 Compression                     15 min

Week 2 (Days 3-4):  Advanced Performance
- 2.6 Async Tasks                     2 hours
- 2.8 DB Optimization                 2 hours

Week 3 (Day 1-2):   Monitoring
- 2.9 Error Tracking                  1 hour
- 2.10 Metrics                        2 hours

Week 3 (Day 3-5):   Testing & Deployment
- Testing & Verification              2 hours
- Deploy to Staging/Prod              Continuous
────────────────────────────────────
Total: ~14 hours
```

---

## 🎯 Recommended Start: Path C (Balanced)

### Why Balanced?
- ✅ Addresses critical security gaps
- ✅ Delivers noticeable performance improvements
- ✅ Enables production-grade monitoring
- ✅ Spreads work across 3 weeks
- ✅ Allows for testing between phases

---

## 📊 Expected Outcomes by Component

| Component | Current | After Phase 2 | Improvement |
|-----------|---------|---------------|------------|
| **Security Score** | 8.5/10 | 9.5/10 | +1.0 |
| **API Latency** | 112ms | <80ms | ⬇️ 28% |
| **Cache Hit Rate** | 0% | 60% | ⬆️ 60% |
| **Payload Size** | 100% | 30% | ⬇️ 70% |
| **Error Visibility** | ❌ None | ✅ Sentry | ✅ Full |
| **Metrics Available** | ❌ None | ✅ Prometheus | ✅ Full |
| **Response Time P95** | 250ms+ | <150ms | ⬇️ 40% |

---

## 🔧 Phase 2 Setup Tasks (Do These First)

### Task 1: Install Docker & Docker Compose (30 min)
**Required for**: Redis, monitoring stack

```bash
# Windows/Mac: Download Docker Desktop
# https://www.docker.com/products/docker-desktop

# Ubuntu/Debian
sudo apt-get install docker.io docker-compose

# Verify installation
docker --version
docker-compose --version
```

### Task 2: Create docker-compose.yml (15 min)
**Location**: Project root

```yaml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    networks:
      - biomech

  # Optional: Prometheus for metrics
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - biomech

  # Optional: Grafana for dashboards
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - biomech
    depends_on:
      - prometheus

volumes:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  biomech:
    driver: bridge
```

### Task 3: Start Infrastructure (5 min)

```bash
# Start all services
docker-compose up -d

# Verify services running
docker-compose ps

# View logs
docker-compose logs -f redis

# Access services
# Redis: localhost:6379
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
```

### Task 4: Update Requirements (10 min)

Add to `backend/requirements.txt`:

```
# Phase 2: Security & Performance

# Caching
redis==5.0.0
aioredis==2.0.1

# Security
google-cloud-secret-manager==2.16.0

# Monitoring
sentry-sdk[fastapi]==1.39.0
prometheus-client==0.19.0

# Async processing (optional)
celery==5.3.4
```

Then install:
```bash
pip install -r backend/requirements.txt
```

---

## 📝 Week-by-Week Implementation Plan

### WEEK 1: Days 1-3 (Security Foundation)

#### Monday: 2.1 API Key Management (2 hours)

```bash
# Step 1: Create GCP project (if needed)
gcloud projects create biomech-ai-prod

# Step 2: Set up Secret Manager
gcloud services enable secretmanager.googleapis.com

# Step 3: Create secrets
echo -n "your-gemini-key" | gcloud secrets create gemini-api-key --data-file=-
echo -n "your-supabase-key" | gcloud secrets create supabase-key --data-file=-

# Step 4: Grant service account access
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# Step 5: Update backend/main.py with code from PHASE_2_IMPLEMENTATION.md section 2.1
```

#### Tuesday: 2.2 + 2.3 (Request Limits & Headers - 1.5 hours)

```python
# Update backend/main.py with:
# - MAX_REQUEST_SIZE middleware (section 2.2)
# - Security headers middleware (section 2.3)
# - Test locally with curl (commands in file)
```

#### Wednesday: 2.4 Database Security (1 hour)

```sql
-- Run in Supabase SQL editor:
-- Copy/paste SQL from PHASE_2_IMPLEMENTATION.md section 2.4
-- Test with direct queries
```

**By End of Week 1**: Security foundation complete ✅

---

### WEEK 2: Days 1-5 (Performance Optimization)

#### Monday: 2.5 Redis Caching (3 hours)

```bash
# Step 1: Start Redis
docker-compose up -d redis

# Step 2: Install Redis CLI
# macOS: brew install redis
# Ubuntu: sudo apt-get install redis-tools

# Step 3: Verify connection
redis-cli ping  # Should return PONG

# Step 4: Copy caching code from PHASE_2_IMPLEMENTATION.md section 2.5 to:
# - backend/cache.py (new file)
# - Update backend/main.py to use cache

# Step 5: Test
redis-cli KEYS "*"  # Should see cache keys
```

#### Tuesday: 2.6 + 2.7 (Async & Compression - 2 hours)

```python
# Add to backend/main.py:
# - GZIPMiddleware (section 2.7 - already mostly configured)
# - Background tasks for video processing (section 2.6)
# - New async task status endpoint
```

#### Wednesday-Friday: 2.8 (Database Optimization - 2 hours)

```sql
-- Step 1: Create indexes (run in Supabase)
-- Copy/paste from PHASE_2_IMPLEMENTATION.md section 2.8

-- Step 2: Analyze query performance
SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC;

-- Step 3: Update Python queries with optimizations from section 2.8
```

**By End of Week 2**: Performance optimization complete ✅

---

### WEEK 3: Days 1-5 (Monitoring & Testing)

#### Monday: 2.9 Error Tracking (1 hour)

```bash
# Step 1: Create Sentry account
# https://sentry.io/signup/

# Step 2: Create project "biomech-ai"

# Step 3: Get DSN from settings

# Step 4: Add to .env
SENTRY_DSN=https://your-dsn@sentry.io/project-id

# Step 5: Update backend/main.py with Sentry initialization (section 2.9)

# Step 6: Test
# Make an error request and verify it appears in Sentry
```

#### Tuesday: 2.10 Metrics (2 hours)

```python
# Step 1: Copy metrics code to backend/metrics.py
# Step 2: Update backend/main.py with metrics middleware
# Step 3: Test: curl http://localhost:8000/metrics
# Step 4: Create Grafana dashboard (optional)
```

#### Wednesday: Performance Benchmarking (2 hours)

```bash
# Step 1: Install artillery
npm install -g artillery

# Step 2: Create load-test.yml (from PHASE_2_IMPLEMENTATION.md)

# Step 3: Run baseline test
artillery run load-test.yml

# Step 4: Compare results against Phase 1 metrics
# Expected: 28% latency reduction, 60% uptime, <0.1% error rate
```

#### Thursday-Friday: Integration Testing (2 hours)

```bash
# Test all Phase 2 features together:
# 1. CORS + Rate Limiting (Phase 1)
# 2. Cache effectiveness
# 3. Error tracking in Sentry
# 4. Metrics in Prometheus
# 5. Compression in responses
# 6. Async job status tracking
```

**By End of Week 3**: Monitoring & testing complete ✅

---

## 🧪 Phase 2 Testing Checklist

- [ ] **Security Tests**
  - [ ] Request size limit enforced (send 20MB file, should get 413)
  - [ ] API keys loaded from Secret Manager (not .env)
  - [ ] Security headers present in responses
  - [ ] RLS policies working (unauthorized access denied)

- [ ] **Caching Tests**
  - [ ] Redis connection working
  - [ ] Cache keys generated correctly
  - [ ] Cache hits recorded (check redis-cli)
  - [ ] Cache expiration working
  - [ ] Cache hit rate > 50%

- [ ] **Async Tests**
  - [ ] Video upload returns task_id immediately
  - [ ] Status endpoint returns "processing" initially
  - [ ] Status endpoint returns results when complete
  - [ ] Failed tasks show error message

- [ ] **Performance Tests**
  - [ ] Response latency < 80ms (was 112ms)
  - [ ] Compressed responses are 70% smaller
  - [ ] Database queries use indexes (EXPLAIN plan shows Index Scan)
  - [ ] Load test: 1000 concurrent users with <5% error rate

- [ ] **Monitoring Tests**
  - [ ] Errors appear in Sentry within 1 minute
  - [ ] Metrics visible at /metrics endpoint
  - [ ] Prometheus scrapes metrics successfully
  - [ ] Grafana dashboard displays metrics

---

## 📊 Success Metrics: Phase 2 Complete

You'll know Phase 2 is successful when:

```
✅ Security Score: 9.5/10 (up from 8.5/10)
✅ API Latency: <80ms (down from 112ms) 
✅ Cache Hit Rate: >60%
✅ Payload Compression: 70%
✅ Error Tracking: All errors in Sentry
✅ Performance Visible: Metrics in Prometheus/Grafana
✅ No Critical Vulnerabilities: Security audit pass
```

---

## 🆘 Getting Stuck?

### Issue: Redis connection timeout
```bash
# Check Redis is running
docker-compose ps redis
# Should show "Up"

# Check Redis logs
docker-compose logs redis

# Restart Redis
docker-compose restart redis
```

### Issue: Secret Manager failing
```
Error: Failed to retrieve secret gemini-api-key
```
**Solution**: Ensure service account has secretAccessor role
```bash
gcloud projects get-iam-policy PROJECT_ID
```

### Issue: Cache not working
```python
# Add debug logging
logger.debug(f"Cache key: {key}")
logger.debug(f"Cache hit: {cached is not None}")
```

---

## 📞 Resources

- **PHASE_2_IMPLEMENTATION.md** - Detailed technical guide
- **Docker Compose Docs** - https://docs.docker.com/compose/
- **Redis Documentation** - https://redis.io/documentation
- **Sentry Docs** - https://docs.sentry.io/platforms/python/integrations/fastapi/
- **Prometheus Docs** - https://prometheus.io/docs/

---

## ✅ Ready to Start Phase 2?

1. **Choose Your Path**: Security First / Performance First / Balanced
2. **Setup Infrastructure**: Docker, Redis, configs
3. **Follow Implementation Flow**: Week 1 → Week 2 → Week 3
4. **Test & Verify**: Use testing checklist
5. **Monitor & Optimize**: Watch metrics in Phase 3

**Recommended Start**: Security First Path (Day 1-2) then Performance Path (Day 3-5)

---

**Let's make Biomech AI elite! 🚀**

Choose your starting point:
1. **Start with Security** (2.1-2.4) - 4.5 hours
2. **Start with Caching** (2.5) - 3 hours (biggest perf boost)
3. **Follow Balanced Path** (all of above) - 14 hours

What's your team's priority?
