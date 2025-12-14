"""
Cache module - Strategy Pattern implementation for caching.

Design Patterns Used:
- Strategy Pattern: Interchangeable cache backends
- Factory Pattern: CacheManager creates appropriate strategy

Available Strategies:
- MemoryCacheStrategy: In-memory caching (dev/fallback)
- RedisCacheStrategy: Redis-based caching (production)
"""

from app.services.cache.base import BaseCacheStrategy
from app.services.cache.memory_cache import MemoryCacheStrategy
from app.services.cache.redis_cache import RedisCacheStrategy
from app.services.cache.cache_manager import CacheManager

__all__ = [
    "BaseCacheStrategy",
    "MemoryCacheStrategy",
    "RedisCacheStrategy",
    "CacheManager",
]
