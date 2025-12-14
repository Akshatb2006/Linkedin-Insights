"""
Cache Strategy - Base interface and common utilities.

Implements Strategy Pattern for caching operations.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseCacheStrategy(ABC):
    """
    Abstract base class for cache strategies.
    
    Design Pattern: Strategy Pattern
    - Defines a family of algorithms (cache backends)
    - Makes them interchangeable
    - Lets the algorithm vary independently from clients
    
    SOLID Principles:
    - SRP: Each cache strategy handles only its specific backend
    - OCP: New strategies can be added without modifying existing code
    - LSP: All strategies can be substituted for the base class
    """
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache strategy.
        
        Args:
            default_ttl: Default time-to-live in seconds (5 minutes)
        """
        self.default_ttl = default_ttl
        self._initialized = False
    
    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Get the backend name for this strategy."""
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the cache connection."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close the cache connection."""
        pass
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store a value in cache with optional TTL."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        pass
    
    @abstractmethod
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern."""
        pass
    
    @abstractmethod
    async def get_stats(self) -> dict:
        """Get cache statistics."""
        pass
    
    def _make_key(self, prefix: str, identifier: str) -> str:
        """Generate a namespaced cache key."""
        return f"linkedin_insights:{prefix}:{identifier}"
