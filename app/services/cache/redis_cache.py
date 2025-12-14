"""
Redis Cache Strategy - Redis-based caching implementation.

Provides distributed caching for production deployments.
"""

import json
from typing import Any, Optional

from app.services.cache.base import BaseCacheStrategy


class RedisCacheStrategy(BaseCacheStrategy):
    """
    Redis cache strategy using redis-py async client.
    
    Design Pattern: Strategy Pattern (Concrete Strategy)
    
    Best for:
    - Production deployments
    - Multi-instance applications
    - Persistent caching across restarts
    
    Features:
    - Distributed across instances
    - Persistent (optional)
    - Pattern-based key operations
    """
    
    def __init__(self, redis_url: str, default_ttl: int = 300):
        super().__init__(default_ttl)
        self._redis_url = redis_url
        self._client = None
    
    @property
    def backend_name(self) -> str:
        return "redis"
    
    async def initialize(self) -> None:
        """Initialize Redis connection."""
        try:
            import redis.asyncio as redis
            self._client = redis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self._client.ping()
            self._initialized = True
            print(f"✅ Connected to Redis: {self._redis_url}")
        except Exception as e:
            print(f"⚠️ Redis connection failed: {e}")
            raise
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
        self._initialized = False
        print("🔌 Redis connection closed")
    
    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from Redis."""
        if not self._client:
            return None
        
        try:
            value = await self._client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            print(f"⚠️ Redis get error: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store a value in Redis with TTL."""
        if not self._client:
            return False
        
        ttl = ttl or self.default_ttl
        
        try:
            serialized = json.dumps(value, default=str)
            await self._client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"⚠️ Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete a value from Redis."""
        if not self._client:
            return False
        
        try:
            result = await self._client.delete(key)
            return result > 0
        except Exception as e:
            print(f"⚠️ Redis delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        if not self._client:
            return False
        
        try:
            return await self._client.exists(key) > 0
        except Exception as e:
            print(f"⚠️ Redis exists error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern."""
        if not self._client:
            return 0
        
        try:
            keys = await self._client.keys(pattern)
            if keys:
                return await self._client.delete(*keys)
            return 0
        except Exception as e:
            print(f"⚠️ Redis clear error: {e}")
            return 0
    
    async def get_stats(self) -> dict:
        """Get Redis statistics."""
        if not self._client:
            return {
                "backend": self.backend_name,
                "error": "Not connected",
                "ttl_seconds": self.default_ttl,
            }
        
        try:
            info = await self._client.info("memory")
            keys_count = await self._client.dbsize()
            return {
                "backend": self.backend_name,
                "entries": keys_count,
                "memory_used": info.get("used_memory_human", "unknown"),
                "ttl_seconds": self.default_ttl,
                "connected": True,
            }
        except Exception as e:
            return {
                "backend": self.backend_name,
                "error": str(e),
                "ttl_seconds": self.default_ttl,
            }
