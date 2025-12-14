import json
import hashlib
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from app.config import get_settings


@dataclass
class CacheEntry:
    value: Any
    expires_at: datetime


class CacheService:
    _redis_client = None
    _memory_cache: Dict[str, CacheEntry] = {}
    _initialized = False
    _use_memory = False
    
    @classmethod
    async def initialize(cls) -> None:
        if cls._initialized:
            return
        
        settings = get_settings()
        
        if not settings.cache_enabled:
            print("📦 Caching disabled by configuration")
            cls._use_memory = True
            cls._initialized = True
            return
        
        try:
            import redis.asyncio as redis
            cls._redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await cls._redis_client.ping()
            print(f"✅ Connected to Redis: {settings.redis_url}")
            cls._initialized = True
        except Exception as e:
            print(f"⚠️ Redis not available: {e}")
            print("📦 Using in-memory cache fallback")
            cls._use_memory = True
            cls._initialized = True
    
    @classmethod
    async def close(cls) -> None:
        if cls._redis_client:
            await cls._redis_client.close()
            cls._redis_client = None
        cls._memory_cache.clear()
        cls._initialized = False
        print("🔌 Cache connection closed")
    
    @classmethod
    def _generate_key(cls, prefix: str, identifier: str) -> str:
        return f"linkedin_insights:{prefix}:{identifier}"
    
    @classmethod
    def _serialize(cls, value: Any) -> str:
        return json.dumps(value, default=str)
    
    @classmethod
    def _deserialize(cls, value: str) -> Any:
        return json.loads(value)
    
    @classmethod
    async def get(cls, prefix: str, identifier: str) -> Optional[Any]:
        if not cls._initialized:
            await cls.initialize()
        
        key = cls._generate_key(prefix, identifier)
        
        if cls._use_memory:
            return cls._get_from_memory(key)
        
        try:
            value = await cls._redis_client.get(key)
            if value:
                return cls._deserialize(value)
        except Exception as e:
            print(f"⚠️ Cache get error: {e}")
        
        return None
    
    @classmethod
    async def set(
        cls, 
        prefix: str, 
        identifier: str, 
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        if not cls._initialized:
            await cls.initialize()
        
        settings = get_settings()
        ttl = ttl or settings.cache_ttl
        key = cls._generate_key(prefix, identifier)
        
        if cls._use_memory:
            return cls._set_in_memory(key, value, ttl)
        
        try:
            serialized = cls._serialize(value)
            await cls._redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"⚠️ Cache set error: {e}")
            return False
    
    @classmethod
    async def delete(cls, prefix: str, identifier: str) -> bool:
        if not cls._initialized:
            await cls.initialize()
        
        key = cls._generate_key(prefix, identifier)
        
        if cls._use_memory:
            return cls._delete_from_memory(key)
        
        try:
            await cls._redis_client.delete(key)
            return True
        except Exception as e:
            print(f"⚠️ Cache delete error: {e}")
            return False
    
    @classmethod
    async def clear_all(cls, prefix: Optional[str] = None) -> int:
        if not cls._initialized:
            await cls.initialize()
        
        if cls._use_memory:
            if prefix:
                pattern = f"linkedin_insights:{prefix}:"
                keys_to_delete = [k for k in cls._memory_cache.keys() if k.startswith(pattern)]
                for key in keys_to_delete:
                    del cls._memory_cache[key]
                return len(keys_to_delete)
            else:
                count = len(cls._memory_cache)
                cls._memory_cache.clear()
                return count
        
        try:
            pattern = f"linkedin_insights:{prefix}:*" if prefix else "linkedin_insights:*"
            keys = await cls._redis_client.keys(pattern)
            if keys:
                await cls._redis_client.delete(*keys)
            return len(keys)
        except Exception as e:
            print(f"⚠️ Cache clear error: {e}")
            return 0
    
    @classmethod
    def _get_from_memory(cls, key: str) -> Optional[Any]:
        entry = cls._memory_cache.get(key)
        if entry:
            if datetime.now() < entry.expires_at:
                return entry.value
            else:
                del cls._memory_cache[key]
        return None
    
    @classmethod
    def _set_in_memory(cls, key: str, value: Any, ttl: int) -> bool:
        expires_at = datetime.now() + timedelta(seconds=ttl)
        cls._memory_cache[key] = CacheEntry(value=value, expires_at=expires_at)
        return True
    
    @classmethod
    def _delete_from_memory(cls, key: str) -> bool:
        if key in cls._memory_cache:
            del cls._memory_cache[key]
            return True
        return False
    
    @classmethod
    async def get_stats(cls) -> Dict[str, Any]:
        if not cls._initialized:
            await cls.initialize()
        
        settings = get_settings()
        
        if cls._use_memory:
            now = datetime.now()
            expired_keys = [k for k, v in cls._memory_cache.items() if now >= v.expires_at]
            for key in expired_keys:
                del cls._memory_cache[key]
            
            return {
                "backend": "memory",
                "entries": len(cls._memory_cache),
                "ttl_seconds": settings.cache_ttl,
                "enabled": settings.cache_enabled,
            }
        
        try:
            info = await cls._redis_client.info("memory")
            keys_count = await cls._redis_client.dbsize()
            return {
                "backend": "redis",
                "entries": keys_count,
                "memory_used": info.get("used_memory_human", "unknown"),
                "ttl_seconds": settings.cache_ttl,
                "enabled": settings.cache_enabled,
            }
        except Exception as e:
            return {
                "backend": "redis",
                "error": str(e),
                "ttl_seconds": settings.cache_ttl,
                "enabled": settings.cache_enabled,
            }
