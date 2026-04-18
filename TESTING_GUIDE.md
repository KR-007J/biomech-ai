# 🧪 BIOMECH AI — TESTING & VALIDATION GUIDE

After all 5 fixes have been applied, follow these tests to verify everything works.

---

## Prerequisites

```bash
# Install latest dependencies
pip install -r backend/requirements.txt

# Ensure you have curl installed (for testing)
# Windows: comes with WSL or use Invoke-WebRequest in PowerShell
# Mac: brew install curl
# Linux: apt-get install curl
```

---

## TEST 1: CORS Security ✅

### What We're Testing
- CORS now rejects requests from unauthorized origins
- Only allows specified domains from `.env`

### Run This Test

```bash
# Start the backend
cd backend
uvicorn main:app --reload

# In another terminal, test unauthorized origin
curl -X OPTIONS http://localhost:8000 \
  -H "Origin: https://evil.com" \
  -H "Access-Control-Request-Method: POST" \
  -v

# Expected: NO "Access-Control-Allow-Origin" header in response
# ✅ PASS: No CORS headers for unauthorized origin
# ❌ FAIL: If "Access-Control-Allow-Origin: https://evil.com" appears
```

### Test Authorized Origin

```bash
# Test with authorized local origin
curl -X OPTIONS http://localhost:8000 \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -v

# Expected: "Access-Control-Allow-Origin: http://localhost:3000"
```

---

## TEST 2: Rate Limiting ✅

### What We're Testing
- API should allow 10 requests per minute
- After 10 requests, should return 429 Too Many Requests

### Run This Test (PowerShell)

```powershell
# Make 15 rapid requests
for ($i = 1; $i -le 15; $i++) {
  Write-Host "Request $i..."
  $response = Invoke-WebRequest -Uri http://localhost:8000/generate-feedback `
    -Method POST `
    -ContentType "application/json" `
    -Body '{
      "metrics": {
        "angles": {"left_knee": 90, "right_knee": 95},
        "deviations": {"left_knee": 0, "right_knee": 0},
        "pose_confidence": 0.9
      },
      "exercise_type": "squat"
    }' `
    -ErrorAction Continue
  
  Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
}

# Expected: 
# Requests 1-10: Status 200
# Requests 11-15: Status 429
```

### Run This Test (Bash)

```bash
for i in {1..15}; do
  echo "Request $i..."
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/generate-feedback \
    -H "Content-Type: application/json" \
    -d '{
      "metrics": {
        "angles": {"left_knee": 90, "right_knee": 95},
        "deviations": {"left_knee": 0, "right_knee": 0},
        "pose_confidence": 0.9
      },
      "exercise_type": "squat"
    }')
  echo "Status: $STATUS"
done

# Requests 1-10 should return: 200
# Requests 11-15 should return: 429
```

---

## TEST 3: Input Validation ✅

### What We're Testing
- Invalid requests now return 422 Unprocessable Entity
- Valid requests work as before

### Test Invalid Input (Missing Required Field)

```bash
curl -X POST http://localhost:8000/generate-feedback \
  -H "Content-Type: application/json" \
  -d '{
    "metrics": {
      "angles": {"left_knee": 90},
      "deviations": {}
      # Missing "pose_confidence" required field
    },
    "exercise_type": "squat"
  }'

# Expected: 422 Unprocessable Entity with error details
# ✅ PASS: Returns 422 with validation error
```

### Test Invalid Exercise Type

```bash
curl -X POST http://localhost:8000/generate-feedback \
  -H "Content-Type: application/json" \
  -d '{
    "metrics": {
      "angles": {"left_knee": 90, "right_knee": 95},
      "deviations": {"left_knee": 0, "right_knee": 0},
      "pose_confidence": 0.9
    },
    "exercise_type": ""  # Empty string - invalid
  }'

# Expected: 422 Unprocessable Entity
```

### Test Valid Request

```bash
curl -X POST http://localhost:8000/generate-feedback \
  -H "Content-Type: application/json" \
  -d '{
    "metrics": {
      "angles": {"left_knee": 90, "right_knee": 95},
      "deviations": {"left_knee": 0, "right_knee": 0},
      "pose_confidence": 0.95
    },
    "exercise_type": "squat",
    "user_id": "user123"
  }'

# Expected: 200 OK with proper response structure
```

---

## TEST 4: Logging & Error Handling ✅

### What We're Testing
- All operations are logged with proper severity
- Errors include context (user_id, exercise_type, etc.)
- No more silent failures

### Run This Test

```bash
# Start backend with logging visible
cd backend
uvicorn main:app --reload

# In another terminal, make various requests
# Watch the terminal logs for:

# ✅ SUCCESS: You should see logs like:
# 2026-04-17 10:30:45,123 - __main__ - INFO - Feedback request received: exercise=squat, user=user123
# 2026-04-17 10:30:45,234 - __main__ - DEBUG - Risk analysis completed: MEDIUM
# 2026-04-17 10:30:45,340 - __main__ - INFO - AI feedback generated successfully for squat
# 2026-04-17 10:30:45,450 - __main__ - INFO - Analysis report saved to Supabase for user user123

# Trigger an error by sending invalid metrics:
curl -X POST http://localhost:8000/generate-feedback \
  -H "Content-Type: application/json" \
  -d '{
    "metrics": {
      "angles": {},
      "deviations": {},
      "pose_confidence": 1.5  # Invalid: > 1.0
    },
    "exercise_type": "squat"
  }'

# ✅ You should see error logged with details
```

---

## TEST 5: Type Hints & Documentation ✅

### What We're Testing
- All endpoints have proper type hints
- Auto-generated API docs are accurate
- IDE provides proper autocomplete

### View Auto-Generated Docs

```bash
# Start backend
cd backend
uvicorn main:app --reload

# Open in browser:
http://localhost:8000/docs

# Expected:
# - All endpoints listed with proper input/output schemas
# - Request models show required fields
# - Response models show return structure
# - Descriptions are present
```

### Test in IDE (VS Code, PyCharm, etc.)

```python
# Open any Python file that imports from main.py
# Hover over function names - should show full type hints
# Type ctrl+space for autocomplete - should show typed parameters
```

---

## TEST 6: Check Security Score ✅

### Manual Security Checklist

```
✅ CORS: Domain-restricted (not *)
✅ Rate Limiting: 10/minute active  
✅ Validation: Pydantic models with constraints
✅ Logging: All operations logged
✅ Error Handling: Specific exceptions, no bare except
✅ Type Safety: 100% type hints
✅ Secrets: No hardcoded API keys
✅ Supabase: Error handling for DB failures
```

---

## TEST 7: Load Testing (Optional) ✅

### Simple Load Test

```bash
# Test with artillery (install first if needed)
# npm install -g artillery

# Create load-test.yml
cat > load-test.yml << 'EOF'
config:
  target: "http://localhost:8000"
  phases:
    - duration: 30
      arrivalRate: 10
      name: "Steady load"

scenarios:
  - name: "API Load Test"
    flow:
      - post:
          url: "/generate-feedback"
          headers:
            Content-Type: "application/json"
          json:
            metrics:
              angles: {"left_knee": 90, "right_knee": 95}
              deviations: {"left_knee": 0, "right_knee": 0}
              pose_confidence: 0.9
            exercise_type: "squat"
EOF

# Run load test
artillery run load-test.yml
```

---

## TEST 8: Test Response Schema ✅

### Verify Response Structure

```bash
curl -X POST http://localhost:8000/generate-feedback \
  -H "Content-Type: application/json" \
  -d '{
    "metrics": {
      "angles": {"left_knee": 90, "right_knee": 95},
      "deviations": {"left_knee": 0, "right_knee": 0},
      "pose_confidence": 0.95
    },
    "exercise_type": "squat"
  }' | jq .

# Expected response structure:
# {
#   "status": "completed",
#   "timestamp": 1234567890.123,
#   "summary": {
#     "angles": {...},
#     "ideal_ranges": {...},
#     "deviations": {...},
#     "risk": {
#       "risk_level": "LOW",
#       "risk_score": 5.5,
#       "risk_reason": "...",
#       "pose_confidence": 0.95
#     },
#     "pose_confidence": 0.95
#   },
#   "coach_feedback": {
#     "issue": "string",
#     "reason": "string",
#     "fix": "string"
#   },
#   "performance_metrics": {
#     "source": "Biomech-AI-Hardened-Backend",
#     "processing_time_sec": 0.123,
#     "engine_status": "AI_AUGMENTED" | "SAFE_MODE" | "FAILOVER_ACTIVE",
#     "estimated_accuracy": "96.4%"
#   }
# }
```

---

## ✅ PASSING ALL TESTS

Once you've verified all tests pass:

1. **Deploy to Staging**
   - Test against your staging environment
   - Verify logs are being collected
   - Monitor for any unexpected errors

2. **Deploy to Production**
   - Update `.env` with production origins
   - Monitor first hour for issues
   - Check logs for any anomalies

3. **Monitor Metrics**
   - Track API response times
   - Monitor error rates
   - Track rate limit hits (should be rare)

---

## 🆘 Troubleshooting

### CORS Tests Failing?
- Check `.env` for `ALLOWED_ORIGINS`
- Verify origins are separated by commas
- Restart backend after changing `.env`

### Rate Limiting Not Working?
- Check if `slowapi` is installed: `pip list | grep slowapi`
- Verify decorators are on endpoints
- Clear browser cache (might cache 429 responses)

### Validation Not Triggering?
- Make sure Pydantic models are defined
- Check ContentType header is `application/json`
- Verify field names match exactly

### No Logs Appearing?
- Check log level in code (should be INFO)
- Ensure terminal hasn't hit line limit
- Redirect logs to file if needed: `uvicorn main:app > app.log 2>&1`

---

## 📊 Success Metrics

After all fixes:

| Metric | Target | How to Verify |
|--------|--------|---------------|
| CORS | Restricted | TEST 1 |
| Rate Limit | 10/min enforced | TEST 2 |
| Validation | 100% coverage | TEST 3 |
| Logging | All operations | TEST 4 |
| Type Safety | 100% | TEST 5 |
| Response | Proper schema | TEST 8 |
| Security | 8.5/10 | All tests |

---

**Ready to test? Start with TEST 1 and work your way through!** 🚀
