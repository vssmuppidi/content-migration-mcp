"""Context caching service for performance optimization."""

import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta


class ContextCache:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self):
        """Initialize the cache."""
        self._cache: Dict[str, Tuple[Any, float, float]] = {}  # key -> (value, timestamp, ttl)
        self._hits = 0
        self._misses = 0
        self._max_size = 1000  # Maximum number of entries
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value if found and not expired, None otherwise
        """
        if key not in self._cache:
            self._misses += 1
            return None
        
        value, timestamp, ttl = self._cache[key]
        age = time.time() - timestamp
        
        if age > ttl:
            # Expired, remove from cache
            del self._cache[key]
            self._misses += 1
            return None
        
        self._hits += 1
        return value
    
    def set(self, key: str, value: Any, ttl: float = 3600.0):
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 1 hour)
        """
        # Evict old entries if cache is full
        if len(self._cache) >= self._max_size:
            self._evict_expired()
            # If still full, remove oldest 10% of entries
            if len(self._cache) >= self._max_size:
                self._evict_oldest(int(self._max_size * 0.1))
        
        self._cache[key] = (value, time.time(), ttl)
    
    def delete(self, key: str):
        """Delete a key from the cache."""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
    
    def _evict_expired(self):
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp, ttl) in self._cache.items()
            if current_time - timestamp > ttl
        ]
        for key in expired_keys:
            del self._cache[key]
    
    def _evict_oldest(self, count: int):
        """Evict the oldest entries from cache."""
        # Sort by timestamp and remove oldest
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1][1]  # Sort by timestamp
        )
        for key, _ in sorted_entries[:count]:
            del self._cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
        
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "total_requests": total_requests
        }
    
    def cleanup(self):
        """Clean up expired entries."""
        self._evict_expired()


# Global cache instance
_cache = ContextCache()


def get_cache() -> ContextCache:
    """Get the global cache instance."""
    return _cache


def cache_key_for_topic(topic: str, sources: list) -> str:
    """Generate cache key for a topic and sources."""
    sources_str = "_".join(sorted(sources))
    return f"trending:{topic}:{sources_str}"


def cache_key_for_query_analysis(query: str) -> str:
    """Generate cache key for query analysis."""
    # Normalize query (lowercase, strip)
    normalized = query.lower().strip()
    return f"query_analysis:{hash(normalized)}"


def cache_key_for_context_summary(topic: str, sources: list) -> str:
    """Generate cache key for context summary."""
    sources_str = "_".join(sorted(sources))
    return f"context_summary:{topic}:{sources_str}"

