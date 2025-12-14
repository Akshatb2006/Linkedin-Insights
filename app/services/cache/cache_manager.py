"""
Cache Manager - Factory for creating and managing cache strategies.

Implements Factory Pattern to create appropriate cache strategy based on configuration.
"""

from typing import Optional

from app.config import get_settings
from app.services.cache.base import BaseCacheStrategy
from app.services.cache.memory_cache import MemoryCacheStrategy
from app.services.cache.redis_cache import RedisCacheStrategy


class CacheManager:
    """
    Cache Manager - Factory and Facade for cache operations.
    
    Design Patterns:
    - Factory Pattern: Creates appropriate cache strategy
    - Facade Pattern: Provides simple interface to cache operations
    - Singleton Pattern: Single instance of active strategy
    
    SOLID Principles:
    - SRP: Only manages cache strategy lifecycle
    - OCP: New strategies can be added without modifying this class
    - DIP: Depends on BaseCacheStrategy abstraction
    """
    
    _instance: Optional[BaseCacheStrategy] = None
    _strategy_type: Optional[str] = None
    
    @classmethod
    async def get_strategy(cls) -> BaseCacheStrategy:
        """
        Get the current cache strategy (creates if needed).
        
        Factory Method: Creates appropriate strategy based on config.
        """
        if cls._instance is not None and cls._instance._initialized:
            return cls._instance
        
        settings = get_settings()
        
        if not settings.cache_enabled:
            # Caching disabled - use memory with no-op
            cls._instance = MemoryCacheStrategy(default_ttl=settings.cache_ttl)
            await cls._instance.initialize()
            cls._strategy_type = "disabled"
            return cls._instance
        
        # Try Redis first, fall back to memory
        try:
            strategy = RedisCacheStrategy(
                redis_url=settings.redis_url,
                default_ttl=settings.cache_ttl
            )
            await strategy.initialize()
            cls._instance = strategy
            cls._strategy_type = "redis"
        except Exception as e:
            print(f"⚠️ Redis unavailable, using memory cache: {e}")
            strategy = MemoryCacheStrategy(default_ttl=settings.cache_ttl)
            await strategy.initialize()
            cls._instance = strategy
            cls._strategy_type = "memory"
        
        return cls._instance
    
    @classmethod
    async def close(cls) -> None:
        """Close the current cache strategy."""
        if cls._instance:
            await cls._instance.close()
            cls._instance = None
            cls._strategy_type = None
    
    @classmethod
    def get_strategy_type(cls) -> Optional[str]:
        """Get the current strategy type."""
        return cls._strategy_type
    
    # Convenience methods that delegate to the strategy
    
    @classmethod
    async def get(cls, prefix: str, identifier: str) -> Optional[any]:
        """Get a value from cache."""
        strategy = await cls.get_strategy()
        key = strategy._make_key(prefix, identifier)
        return await strategy.get(key)
    
    @classmethod
    async def set(
        cls,
        prefix: str,
        identifier: str,
        value: any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set a value in cache."""
        strategy = await cls.get_strategy()
        key = strategy._make_key(prefix, identifier)
        return await strategy.set(key, value, ttl)
    
    @classmethod
    async def delete(cls, prefix: str, identifier: str) -> bool:
        """Delete a value from cache."""
        strategy = await cls.get_strategy()
        key = strategy._make_key(prefix, identifier)
        return await strategy.delete(key)
    
    @classmethod
    async def clear_all(cls, prefix: Optional[str] = None) -> int:
        """Clear all cache entries (optionally filtered by prefix)."""
        strategy = await cls.get_strategy()
        pattern = f"linkedin_insights:{prefix}:*" if prefix else "linkedin_insights:*"
        return await strategy.clear_pattern(pattern)
    
    @classmethod
    async def get_stats(cls) -> dict:
        """Get cache statistics."""
        strategy = await cls.get_strategy()
        stats = await strategy.get_stats()
        stats["enabled"] = get_settings().cache_enabled
        return stats
