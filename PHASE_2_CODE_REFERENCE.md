# Example: Phase 2 Implementation Reference
# This file shows HOW to organize your Phase 2 code

# FILE: backend/cache.py
"""
Redis caching utilities for Biomech AI
"""

import json
import hashlib
import logging
from typing import Any, Dict, Optional, Callable
from redis import asyncio as aioredis

logger = logging.getLogger(__name__)

class CacheManager:
    """Manage caching operations with Redis"""
    
    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        self.redis_client = redis_client
        self.enabled = redis_client is not None
    
    @staticmethod
    def generate_key(prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_parts = [prefix]
        
        # Add positional args
        key_parts.extend([str(arg) for arg in args])
        
        # Add keyword args
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        
        # Create hash for consistency
        combined = "|".join(key_parts)
        hash_val = hashlib.md5(combined.encode()).hexdigest()[:8]
        
        return f"{prefix}:{hash_val}"
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.warning(f"Cache read error for {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Dict[str, Any], 
        ttl: int = 3600
    ) -> bool:
        """Set value in cache with TTL"""
        if not self.enabled:
            return False
        
        try:
            await self.redis_client.setex(
                key, 
                ttl, 
                json.dumps(value)
            )
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.warning(f"Cache write error for {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.enabled:
            return False
        
        try:
            await self.redis_client.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for {key}: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        if not self.enabled:
            return 0
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"Cache INVALIDATE: {pattern} ({deleted} keys)")
                return deleted
            return 0
        except Exception as e:
            logger.warning(f"Cache invalidate error for {pattern}: {e}")
            return 0


# FILE: backend/async_tasks.py
"""
Background task handlers for long-running operations
"""

import json
import uuid
import time
import logging
from typing import Any, Dict, Optional
from redis import asyncio as aioredis

logger = logging.getLogger(__name__)

class TaskManager:
    """Manage background task execution and status tracking"""
    
    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        self.redis_client = redis_client
    
    async def create_task(
        self, 
        operation: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new background task
        
        Args:
            operation: Type of operation (e.g., 'video_analysis')
            metadata: Additional context data
        
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        
        task_data = {
            "task_id": task_id,
            "operation": operation,
            "status": "queued",
            "progress": 0,
            "created_at": time.time(),
            "metadata": metadata or {}
        }
        
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    f"task:{task_id}",
                    86400,  # 24 hour TTL
                    json.dumps(task_data)
                )
                logger.info(f"Task created: {task_id} ({operation})")
            except Exception as e:
                logger.error(f"Failed to create task: {e}")
                raise
        
        return task_id
    
    async def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current task status"""
        if not self.redis_client:
            return None
        
        try:
            task_data = await self.redis_client.get(f"task:{task_id}")
            if task_data:
                return json.loads(task_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get task status {task_id}: {e}")
            return None
    
    async def update_progress(
        self, 
        task_id: str,
        progress: int,
        status: str = "processing"
    ) -> bool:
        """Update task progress"""
        if not self.redis_client:
            return False
        
        try:
            task_data = await self.redis_client.get(f"task:{task_id}")
            if task_data:
                data = json.loads(task_data)
                data["progress"] = progress
                data["status"] = status
                
                await self.redis_client.setex(
                    f"task:{task_id}",
                    86400,
                    json.dumps(data)
                )
                logger.debug(f"Task progress: {task_id} [{progress}%]")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            return False
    
    async def complete_task(
        self,
        task_id: str,
        result: Dict[str, Any],
        ttl: int = 3600
    ) -> bool:
        """Mark task as complete with result"""
        if not self.redis_client:
            return False
        
        try:
            task_data = await self.redis_client.get(f"task:{task_id}")
            if task_data:
                data = json.loads(task_data)
                data["status"] = "completed"
                data["progress"] = 100
                data["result"] = result
                data["completed_at"] = time.time()
                
                await self.redis_client.setex(
                    f"task:{task_id}",
                    ttl,  # TTL after completion
                    json.dumps(data)
                )
                logger.info(f"Task completed: {task_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to complete task {task_id}: {e}")
            return False
    
    async def fail_task(self, task_id: str, error: str, ttl: int = 3600) -> bool:
        """Mark task as failed"""
        if not self.redis_client:
            return False
        
        try:
            task_data = await self.redis_client.get(f"task:{task_id}")
            if task_data:
                data = json.loads(task_data)
                data["status"] = "failed"
                data["error"] = error
                data["failed_at"] = time.time()
                
                await self.redis_client.setex(
                    f"task:{task_id}",
                    ttl,
                    json.dumps(data)
                )
                logger.error(f"Task failed: {task_id} - {error}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to mark task failed {task_id}: {e}")
            return False


# FILE: backend/metrics.py
"""
Prometheus metrics for Biomech AI
"""

from prometheus_client import Counter, Histogram, Gauge

# Request metrics
api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0)
)

# Cache metrics
cache_hits = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['operation', 'key_type']
)

cache_misses = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['operation', 'key_type']
)

cache_size = Gauge(
    'cache_size_bytes',
    'Current cache size in bytes'
)

# Analysis metrics
analysis_processing_time = Histogram(
    'analysis_processing_time_seconds',
    'Time to process analysis',
    ['exercise_type'],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

analysis_risk_distribution = Counter(
    'analysis_risk_distribution_total',
    'Distribution of risk levels',
    ['risk_level', 'exercise_type']
)

# Error metrics
errors_total = Counter(
    'errors_total',
    'Total errors',
    ['error_type', 'endpoint']
)

# Task metrics
background_tasks_total = Counter(
    'background_tasks_total',
    'Total background tasks',
    ['operation', 'status']
)

background_task_duration = Histogram(
    'background_task_duration_seconds',
    'Duration of background tasks',
    ['operation'],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0)
)


# FILE: example usage in main.py
"""
Example of how to use these utilities in your FastAPI app
"""

# At startup:
from backend.cache import CacheManager
from backend.async_tasks import TaskManager

cache_manager: Optional[CacheManager] = None
task_manager: Optional[TaskManager] = None

@app.on_event("startup")
async def startup():
    global cache_manager, task_manager, redis_client
    
    # Initialize Redis
    await init_redis()
    
    # Initialize managers
    cache_manager = CacheManager(redis_client)
    task_manager = TaskManager(redis_client)
    
    logger.info("Cache and Task managers initialized")

# In your endpoints:
@app.post("/generate-feedback")
@limiter.limit("10/minute")
async def generate_feedback(request: Request, payload: FeedbackRequest) -> AnalysisResponse:
    """Generate feedback with caching"""
    start_time = time.time()
    metrics_dict = payload.metrics.dict()
    exercise_type = payload.exercise_type
    
    # Check cache
    cache_key = CacheManager.generate_key(
        "analysis",
        hashlib.md5(json.dumps(metrics_dict).encode()).hexdigest(),
        exercise_type
    )
    
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        cache_hits.labels(operation="analysis", key_type="full").inc()
        return AnalysisResponse(**cached_result)
    
    cache_misses.labels(operation="analysis", key_type="full").inc()
    
    # ... normal processing ...
    
    # Cache result
    await cache_manager.set(cache_key, report.dict(), ttl=3600)
    
    return report
