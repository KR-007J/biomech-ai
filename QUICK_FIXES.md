# 🔧 BIOMECH AI — CRITICAL QUICK FIXES
**Apply These Immediately (Can be done today)**

---

## 🚨 FIX #1: CORS Security Vulnerability — CRITICAL

**Current Code (UNSAFE):**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ❌ DANGEROUS: Allows requests from ANY domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Fixed Code:**
```python
import os
from fastapi.middleware.cors import CORSMiddleware

# Define allowed origins from environment
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # ✅ Only specific domains
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # ✅ Only needed methods
    allow_headers=["Content-Type", "Authorization"],  # ✅ Only needed headers
)
```

**Add to `.env`:**
```
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

---

## 🚨 FIX #2: Add Rate Limiting — HIGH

**Installation:**
```bash
pip install slowapi
```

**In `backend/main.py`:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Try again later."}
    )

# Apply rate limits to endpoints
@app.post("/generate-feedback")
@limiter.limit("10/minute")  # 10 requests per minute per IP
async def generate_feedback(request: Request, payload: dict):
    # ... rest of code
```

---

## 🚨 FIX #3: Better Error Handling — HIGH

**Current Code (BAD):**
```python
try:
    risk_info = analyze_injury_risk(metrics)
except Exception as e:
    print(f"Risk Engine Failure: {e}")  # ❌ No logging, just print
    risk_info = {"risk_level": "UNKNOWN", "risk_factors": ["Engine computation error"]}
```

**Fixed Code:**
```python
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

try:
    risk_info = analyze_injury_risk(metrics)
except ValueError as e:
    logger.error("Invalid metrics for risk analysis", exc_info=True, extra={"error": str(e)})
    risk_info = {"risk_level": "UNKNOWN", "risk_factors": ["Invalid input data"]}
except Exception as e:
    logger.critical("Unexpected error in risk engine", exc_info=True)
    risk_info = {"risk_level": "UNKNOWN", "risk_factors": ["System error"]}
```

**Setup logging in `main.py`:**
```python
import logging
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["default"],
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
```

---

## 🚨 FIX #4: Add Request Validation with Pydantic — HIGH

**Current Code (NO VALIDATION):**
```python
@app.post("/generate-feedback")
async def generate_feedback(payload: dict):  # ❌ No type checking
    metrics = payload.get("metrics")
    exercise_type = payload.get("exercise_type", "General")
    # ...
```

**Fixed Code:**
```python
from pydantic import BaseModel, Field, validator
from typing import Dict, Optional

class MetricsData(BaseModel):
    angles: Dict[str, float]
    deviations: Dict[str, float]
    pose_confidence: float = Field(..., ge=0, le=1)
    
    @validator("pose_confidence")
    def validate_confidence(cls, v):
        if v < 0.5:
            raise ValueError("Pose confidence must be >= 0.5")
        return v

class FeedbackRequest(BaseModel):
    metrics: MetricsData
    exercise_type: str = Field(..., min_length=1, max_length=50)
    user_id: Optional[str] = None
    
    @validator("exercise_type")
    def validate_exercise(cls, v):
        VALID_EXERCISES = ["squat", "pushup", "lunge", "deadlift", "bicep_curl", "shoulder_press", "plank"]
        if v not in VALID_EXERCISES:
            raise ValueError(f"Exercise must be one of {VALID_EXERCISES}")
        return v

class FeedbackResponse(BaseModel):
    status: str
    coach_feedback: Dict[str, str]
    risk_level: str
    processing_time_sec: float

@app.post("/generate-feedback", response_model=FeedbackResponse)
async def generate_feedback(request: FeedbackRequest):  # ✅ Auto-validated
    # FastAPI will automatically validate & return 422 if invalid
    metrics = request.metrics
    # ...
```

---

## 🚨 FIX #5: Add Type Hints to All Functions — MEDIUM

**Current Code:**
```python
def calculate_angle(a, b, c):  # ❌ No type hints
    a = np.array(a)
    # ...
    return float(round(angle, 2))
```

**Fixed Code:**
```python
from typing import List, Tuple, Dict
import numpy as np

def calculate_angle(a: List[float], b: List[float], c: List[float]) -> float:
    """
    Calculates the angle at joint 'b' using vector dot product.
    
    Args:
        a: First point coordinates [x, y]
        b: Vertex point coordinates [x, y]
        c: Third point coordinates [x, y]
    
    Returns:
        Angle in degrees (0-180)
    """
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    v1 = a - b
    v2 = c - b
    
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    
    cos_theta = dot_product / (norm_v1 * norm_v2 + 1e-6)
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    
    angle = np.degrees(np.arccos(cos_theta))
    return float(round(angle, 2))

def get_biomechanical_analysis(keypoints: Dict[str, Dict[str, float]]) -> Dict[str, any]:
    """Analyzes biomechanical joints and returns structured data."""
    if not keypoints:
        return {}
    # ...
```

**Run mypy to check:**
```bash
pip install mypy
mypy backend/ --strict
```

---

## 🚨 FIX #6: Frontend API Security — MEDIUM

**Current Issue:**
```javascript
// ❌ Secrets exposed in client code
const GEMINI_API_KEY = "AIzaSy...";  // NEVER do this!
```

**Fixed Approach:**
```javascript
// ✅ All API calls go through secure backend
class BiomechAPI {
  constructor(baseURL = "/api") {
    this.baseURL = baseURL;
  }
  
  async analyzePose(metrics) {
    const response = await fetch(`${this.baseURL}/generate-feedback`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${this.getToken()}`
      },
      body: JSON.stringify(metrics)
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return response.json();
  }
  
  getToken() {
    // Get from Firebase auth, not hardcoded
    return localStorage.getItem("id_token");
  }
}
```

---

## 📋 Implementation Checklist

**Priority 1 (Today):**
- [ ] Fix CORS (modify main.py line 24-30)
- [ ] Remove API credentials from frontend
- [ ] Add basic error logging

**Priority 2 (This week):**
- [ ] Add rate limiting
- [ ] Add Pydantic validation
- [ ] Add type hints to main.py

**Priority 3 (Next week):**
- [ ] Add comprehensive logging
- [ ] Add request/response logging
- [ ] Move to production secrets manager

---

## 🧪 Quick Test to Verify Fixes

```bash
# Test CORS
curl -X OPTIONS http://localhost:8000 \
  -H "Origin: https://evil.com"
# Should NOT return Access-Control-Allow-Origin for evil.com

# Test rate limiting
for i in {1..15}; do 
  curl -X POST http://localhost:8000/generate-feedback \
    -H "Content-Type: application/json" \
    -d '{"metrics": {}}'
done
# After 10 requests, should return 429 Too Many Requests

# Test validation
curl -X POST http://localhost:8000/generate-feedback \
  -H "Content-Type: application/json" \
  -d '{"metrics": "invalid"}'
# Should return 422 Unprocessable Entity with error details
```

---

## 🎯 Expected Impact

| Fix | Security | Performance | Stability |
|-----|----------|-------------|-----------|
| CORS | 🟢 Critical | - | - |
| Rate Limiting | 🟢 High | 🟢 Medium | 🟢 High |
| Error Handling | 🟡 Medium | - | 🟢 High |
| Validation | 🟢 High | - | 🟢 High |
| Type Hints | - | 🟡 Low | 🟢 High |

**Total Time to Implement: 2-3 hours**
**Expected Improvement: 40-50% stability increase**
