"""
Memory Cache Strategy - In-memory caching implementation.

Provides a lightweight cache for local development or fallback.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from dataclasses import dataclass

from app.services.cache.base import BaseCacheStrategy


@dataclass
class CacheEntry:
    """In-memory cache entry with expiration tracking."""
    value: Any
    expires_at: datetime


class MemoryCacheStrategy(BaseCacheStrategy):
    """
    In-memory cache strategy using a dictionary.
    
    Design Pattern: Strategy Pattern (Concrete Strategy)
    
    Best for:
    - Local development
    - Single-instance deployments
    - Fallback when Redis is unavailable
    
    Limitations:
    - Not shared across processes
    - Lost on restart
    - Memory-bound
    """
    
    def __init__(self, default_ttl: int = 300):
        super().__init__(default_ttl)
        self._cache: Dict[str, CacheEntry] = {}
    
    @property
    def backend_name(self) -> str:
        return "memory"
    
    async def initialize(self) -> None:
        """Initialize in-memory cache."""
        self._cache = {}
        self._initialized = True
        print("📦 Initialized in-memory cache")
    
    async def close(self) -> None:
        """Clear and close in-memory cache."""
        self._cache.clear()
        self._initialized = False
        print("📦 Closed in-memory cache")
    
    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from memory cache."""
        self._cleanup_expired()
        
        entry = self._cache.get(key)
        if entry and datetime.now() < entry.expires_at:
            return entry.value
        
        # Remove expired entry
        if entry:
            del self._cache[key]
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store a value in memory cache."""
        ttl = ttl or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        self._cache[key] = CacheEntry(value=value, expires_at=expires_at)
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete a value from memory cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        entry = self._cache.get(key)
        if entry and datetime.now() < entry.expires_at:
            return True
        return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern (simple prefix match)."""
        self._cleanup_expired()
        
        # Convert simple pattern to prefix match
        prefix = pattern.rstrip("*")
        keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
        
        for key in keys_to_delete:
            del self._cache[key]
        
        return len(keys_to_delete)
    
    async def get_stats(self) -> dict:
        """Get cache statistics."""
        self._cleanup_expired()
        
        return {
            "backend": self.backend_name,
            "entries": len(self._cache),
            "ttl_seconds": self.default_ttl,
            "memory_used": f"{len(str(self._cache))} bytes (approx)",
        }
    
    def _cleanup_expired(self) -> None:
        """Remove expired entries from cache."""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self._cache.items()
            if now >= entry.expires_at
        ]
        for key in expired_keys:
            del self._cache[key]
