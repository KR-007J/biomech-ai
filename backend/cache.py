"""
Redis caching layer for Biomech AI - Phase 2.5 Performance Optimization

Implements distributed caching with automatic expiration, cache invalidation,
and multi-level fallback strategy for improved performance.
"""

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Optional

import redis

logger = logging.getLogger(__name__)


class CacheManager:
    """Distributed cache using Redis with fallback to in-memory"""

    # Default TTL values (in seconds)
    DEFAULT_TTL = 3600  # 1 hour
    SHORT_TTL = 300  # 5 minutes
    LONG_TTL = 86400  # 24 hours

    # Cache key prefixes
    PREFIX_FEEDBACK = "feedback:"
    PREFIX_ANALYSIS = "analysis:"
    PREFIX_USER = "user:"
    PREFIX_SESSION = "session:"

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize Redis connection with fallback"""
        self.redis_enabled = False
        self.redis_client: Optional[redis.Redis] = None
        self.in_memory_cache: dict = {}

        # Try to initialize Redis
        try:
            url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = redis.from_url(url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            self.redis_enabled = True
            logger.info("✅ Redis cache connected successfully")
        except Exception as e:
            logger.warning(
                f"⚠️  Redis not available, falling back to in-memory cache: {e}"
            )
            self.redis_enabled = False

    def _generate_key(self, key_prefix: str, identifier: str) -> str:
        """Generate consistent cache key with prefix"""
        return f"{key_prefix}{hashlib.md5(identifier.encode()).hexdigest()}"

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache"""
        try:
            if self.redis_enabled and self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    logger.debug(f"Cache HIT: {key}")
                    return json.loads(value)

            # Fallback to in-memory
            if key in self.in_memory_cache:
                entry = self.in_memory_cache[key]
                if entry["expires_at"] > datetime.now():
                    logger.debug(f"Cache HIT (in-memory): {key}")
                    return entry["value"]
                else:
                    del self.in_memory_cache[key]

            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> bool:
        """Store value in cache with TTL"""
        try:
            serialized = json.dumps(value)

            if self.redis_enabled and self.redis_client:
                self.redis_client.setex(key, ttl, serialized)
                logger.debug(f"Cache SET (Redis): {key} (TTL: {ttl}s)")
                return True

            # Fallback to in-memory
            self.in_memory_cache[key] = {
                "value": value,
                "expires_at": datetime.now() + timedelta(seconds=ttl),
            }
            logger.debug(f"Cache SET (in-memory): {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            if self.redis_enabled and self.redis_client:
                self.redis_client.delete(key)

            if key in self.in_memory_cache:
                del self.in_memory_cache[key]

            logger.debug(f"Cache DELETE: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern (Redis only)"""
        if not self.redis_enabled or not self.redis_client:
            logger.warning("Pattern invalidation only works with Redis")
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.debug(
                    f"Invalidated {len(keys)} cache entries matching pattern: {pattern}"
                )
            return len(keys)
        except Exception as e:
            logger.error(f"Pattern invalidation error: {e}")
            return 0

    def clear_all(self) -> bool:
        """Clear entire cache (DANGER - use carefully)"""
        try:
            if self.redis_enabled and self.redis_client:
                self.redis_client.flushdb()
            self.in_memory_cache.clear()
            logger.info("⚠️  Cache cleared completely")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

    def get_cache_feedback(self, user_id: str, exercise_type: str) -> Optional[dict]:
        """Get cached feedback for user exercise"""
        key = self._generate_key(self.PREFIX_FEEDBACK, f"{user_id}:{exercise_type}")
        return self.get(key)

    def set_cache_feedback(self, user_id: str, exercise_type: str, feedback: dict):
        """Cache feedback for user exercise"""
        key = self._generate_key(self.PREFIX_FEEDBACK, f"{user_id}:{exercise_type}")
        self.set(key, feedback, ttl=self.SHORT_TTL)

    def invalidate_user_cache(self, user_id: str) -> int:
        """Invalidate all cache entries for a user"""
        if self.redis_enabled:
            return self.invalidate_pattern(f"*{user_id}*")
        return 0

    def get_stats(self) -> dict:
        """Get cache statistics"""
        stats = {
            "redis_enabled": self.redis_enabled,
            "in_memory_entries": len(self.in_memory_cache),
        }

        if self.redis_enabled and self.redis_client:
            try:
                info = self.redis_client.info()
                stats.update(
                    {
                        "redis_used_memory": f"{info.get('used_memory_human', 'N/A')}",
                        "redis_connected_clients": info.get("connected_clients", 0),
                        "redis_keys": self.redis_client.dbsize(),
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to get Redis stats: {e}")

        return stats


# Global cache instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
