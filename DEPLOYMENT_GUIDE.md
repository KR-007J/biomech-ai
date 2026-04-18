# 🚀 Deployment & Operations Guide (Phase 4)

**Version**: 2.0.0-complete  
**Target Environments**: Development, Staging, Production

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Local Development Setup](#local-development-setup)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment (Google Cloud Run)](#cloud-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Environment Configuration](#environment-configuration)
7. [Monitoring & Alerting](#monitoring--alerting)
8. [Scaling & Performance](#scaling--performance)
9. [Disaster Recovery](#disaster-recovery)
10. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### Security
- [ ] All `.env` files excluded from git
- [ ] API keys rotated in production
- [ ] SSL/TLS certificates valid
- [ ] CORS origins configured correctly
- [ ] Database backups enabled
- [ ] Sentry DSN configured

### Testing
- [ ] All tests passing (`pytest test_*.py`)
- [ ] Code coverage > 80%
- [ ] Performance benchmarks acceptable
- [ ] Security scan passed
- [ ] Load test passed (1000 concurrent)

### Infrastructure
- [ ] Redis instance ready
- [ ] Supabase/Database ready
- [ ] Monitoring (Prometheus/Grafana) ready
- [ ] Logging (Sentry) ready
- [ ] CDN configured (if needed)

### Documentation
- [ ] API docs updated
- [ ] Runbooks prepared
- [ ] Change log updated

---

## Local Development Setup

### 1. Prerequisites
```bash
# Python 3.11+
python --version

# Git
git --version

# Docker (optional, for Redis)
docker --version
```

### 2. Clone & Setup
```bash
# Clone repository
git clone https://github.com/biomech-ai/backend.git
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit with your values
nano .env
```

### 4. Start Redis (Optional)
```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or using Homebrew (macOS)
brew install redis
redis-server
```

### 5. Run Application
```bash
# Development mode
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### 6. Test
```bash
# Run all tests
pytest test_*.py -v

# Run with coverage
pytest test_*.py --cov=. --cov-report=html
```

---

## Docker Deployment

### 1. Build Image
```bash
cd backend

# Build single image
docker build -t biomech-ai:latest .

# Build multi-platform
docker buildx build \
  -t biomech-ai:latest \
  --platform linux/amd64,linux/arm64 \
  .
```

### 2. Run Container Locally
```bash
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your_key \
  -e SUPABASE_URL=your_url \
  -e REDIS_URL=redis://host.docker.internal:6379 \
  biomech-ai:latest
```

### 3. Docker Compose (Full Stack)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**docker-compose.yml** already configured with:
- Backend API (port 8000)
- Redis cache (port 6379)
- Prometheus metrics (port 9090)
- Grafana dashboards (port 3000)

---

## Cloud Deployment

### Google Cloud Run

#### 1. Prepare
```bash
# Set project
gcloud config set project biomech-ai-prod

# Enable services
gcloud services enable run.googleapis.com
gcloud services enable container.googleapis.com
```

#### 2. Build & Push to Registry
```bash
# Build
gcloud builds submit --tag gcr.io/biomech-ai-prod/api

# Or manually
docker tag biomech-ai:latest gcr.io/biomech-ai-prod/api:latest
docker push gcr.io/biomech-ai-prod/api:latest
```

#### 3. Deploy
```bash
gcloud run deploy biomech-ai-api \
  --image gcr.io/biomech-ai-prod/api:latest \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --timeout 60 \
  --allow-unauthenticated \
  --set-env-vars="GEMINI_API_KEY=xxx,REDIS_URL=redis://xxx"
```

#### 4. Set Custom Domain
```bash
gcloud run domain-mappings create \
  --service=biomech-ai-api \
  --domain=api.biomech-ai.com
```

---

## Kubernetes Deployment

### 1. Create Deployment Manifest

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: biomech-api
  labels:
    app: biomech-ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: biomech-ai
  template:
    metadata:
      labels:
        app: biomech-ai
    spec:
      containers:
      - name: api
        image: gcr.io/biomech-ai-prod/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: gemini-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: biomech-api-service
spec:
  type: LoadBalancer
  selector:
    app: biomech-ai
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
---
apiVersion: autoscaling.k8s.io/v2
kind: HorizontalPodAutoscaler
metadata:
  name: biomech-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: biomech-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 2. Deploy to Kubernetes
```bash
# Create secrets
kubectl create secret generic api-secrets \
  --from-literal=gemini-key=xxx \
  --from-literal=redis-url=xxx

# Deploy
kubectl apply -f k8s/deployment.yaml

# Check status
kubectl get deployments
kubectl get pods
kubectl logs -f deployment/biomech-api
```

---

## Environment Configuration

### Required Environment Variables

```bash
# API Configuration
PORT=8000
WORKERS=4
ENVIRONMENT=production

# AI & ML
GEMINI_API_KEY=your_gemini_key_here

# Database
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=xxx

# Cache
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET_KEY=your_jwt_secret_key
ALLOWED_ORIGINS=https://app.biomech-ai.com,https://web.biomech-ai.com

# Monitoring
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
PROMETHEUS_PORT=9090

# Logging
LOG_LEVEL=INFO
```

### Configuration Priority
1. Environment variables (highest)
2. `.env` file (development)
3. `.env.example` defaults (fallback)

---

## Monitoring & Alerting

### Prometheus Metrics

```yaml
# prometheus.yml - already configured
scrape_configs:
  - job_name: 'biomech-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Key Metrics to Monitor
- `biomech_request_duration_seconds` - API latency
- `biomech_analysis_requests_total` - Analysis volume
- `biomech_cache_hits_total` / `misses_total` - Cache performance
- `biomech_errors_total` - Error rates
- `biomech_ai_feedback_total` - AI success rate

### Grafana Dashboards

```bash
# Access Grafana
open http://localhost:3000
# Default: admin / admin

# Import dashboards
# - API Performance
# - Cache Statistics
# - Error Trends
# - Resource Usage
```

### Alerting Rules

```yaml
# alerts.yml
groups:
- name: biomech_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(biomech_errors_total[5m]) > 0.05
    for: 5m
    annotations:
      summary: "High error rate detected"
      
  - alert: LowCacheHitRate
    expr: biomech_cache_hits_total / (biomech_cache_hits_total + biomech_cache_misses_total) < 0.3
    for: 10m
    annotations:
      summary: "Cache hit rate below 30%"
      
  - alert: HighLatency
    expr: histogram_quantile(0.95, biomech_request_duration_seconds) > 2
    for: 5m
    annotations:
      summary: "P95 latency above 2 seconds"
```

---

## Scaling & Performance

### Horizontal Scaling
```bash
# Increase replicas
kubectl scale deployment biomech-api --replicas=5

# Auto-scaling (already configured)
# HPA adjusts 3-10 replicas based on CPU usage
```

### Vertical Scaling
```bash
# Increase resources per pod
# Edit deployment.yaml and increase:
# resources.requests.memory
# resources.limits.memory
```

### Performance Optimization
1. **Redis caching**: Already enabled - 60% hit rate expected
2. **GZIP compression**: Enabled for responses > 1KB
3. **Connection pooling**: Configured for Supabase
4. **Query optimization**: Indexes created on analyses table
5. **Rate limiting**: 10/min per IP for expensive endpoints

---

## Disaster Recovery

### Backup Strategy

```bash
# Database backups (Supabase automatic)
# - Daily backups retained 7 days
# - Weekly backups retained 4 weeks
# - Monthly backups retained 12 months

# Manual backup
supabase db pull --project-ref your_project

# Restore from backup
supabase db push
```

### Failover Process

```bash
# 1. Check health status
curl https://api.biomech-ai.com/health

# 2. If down, trigger failover
# - Switch DNS to secondary region
# - Deploy latest image to standby

# 3. Verify
curl https://api.biomech-ai.com/health
```

### Data Recovery

```bash
# List backups
gcloud sql backups list --instance=biomech-api-db

# Restore specific backup
gcloud sql backups restore BACKUP_ID \
  --backup-instance=biomech-api-db
```

---

## Troubleshooting

### Common Issues

#### 1. **High API Latency**
```bash
# Check cache hit rate
curl http://localhost:8000/cache-stats

# Check database query performance
curl http://localhost:9090/graph
# Query: biomech_db_query_duration_seconds

# Scale up replicas
kubectl scale deployment biomech-api --replicas=5
```

#### 2. **High Error Rate**
```bash
# Check error logs
kubectl logs -f deployment/biomech-api

# Check Sentry dashboard
open https://sentry.io/organizations/biomech-ai/

# Review recent deployments
git log --oneline -5
```

#### 3. **OOM Errors**
```bash
# Increase memory limits
# Edit deployment.yaml
resources.limits.memory: "2Gi"

# Check pod memory usage
kubectl top pod -l app=biomech-ai
```

#### 4. **Redis Connection Errors**
```bash
# Check Redis connectivity
redis-cli -u $REDIS_URL ping

# Check Redis memory
redis-cli INFO memory

# Clear old cache if needed
redis-cli FLUSHDB
```

### Debug Commands

```bash
# Test API locally
curl -X GET http://localhost:8000/health

# Check all services
kubectl get all

# View pod logs
kubectl logs -f deployment/biomech-api

# Execute command in pod
kubectl exec -it POD_NAME -- /bin/bash

# Port forward for debugging
kubectl port-forward deployment/biomech-api 8000:8000
```

---

## Runbooks

### Emergency Restart
```bash
# If API is unresponsive:
kubectl delete deployment biomech-api
kubectl apply -f k8s/deployment.yaml
```

### Emergency Cache Clear
```bash
# If cache is corrupted:
redis-cli -u $REDIS_URL FLUSHDB
# API will auto-repopulate
```

### Rollback Deployment
```bash
# View rollout history
kubectl rollout history deployment/biomech-api

# Rollback to previous version
kubectl rollout undo deployment/biomech-api
```

---

## Support & Escalation

**On-Call**: Page via PagerDuty  
**Slack Channel**: #biomech-incidents  
**Email**: ops@biomech-ai.com

---

**Last Updated**: April 2026  
**Deployment Status**: Production-Ready ✅
