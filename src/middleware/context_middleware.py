"""Context injection middleware for monitoring and logging."""

import time
import logging
from typing import Dict, Any, Optional, Callable, List
from functools import wraps

# Setup logging
logging.basicConfig(
    filename='/tmp/mcp_context_middleware.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ContextMiddleware:
    """Middleware for tracking context usage and injection."""
    
    def __init__(self):
        """Initialize the middleware."""
        self.stats = {
            "queries_analyzed": 0,
            "context_fetches": 0,
            "prompt_enrichments": 0,
            "resource_accesses": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    def track_query_analysis(self, query: str, analysis: Dict[str, Any]):
        """Track a query analysis."""
        self.stats["queries_analyzed"] += 1
        logger.info(f"Query analyzed: {query[:50]}... Intent: {analysis.get('intent')}")
    
    def track_context_fetch(self, topic: str, sources: List[str]):
        """Track a context fetch."""
        self.stats["context_fetches"] += 1
        logger.info(f"Context fetched: topic={topic}, sources={sources}")
    
    def track_prompt_enrichment(self, prompt_name: str, query: str):
        """Track a prompt enrichment."""
        self.stats["prompt_enrichments"] += 1
        logger.info(f"Prompt enriched: {prompt_name}, query={query[:50]}...")
    
    def track_resource_access(self, uri: str):
        """Track a resource access."""
        self.stats["resource_accesses"] += 1
        logger.info(f"Resource accessed: {uri}")
    
    def track_cache_hit(self, key: str):
        """Track a cache hit."""
        self.stats["cache_hits"] += 1
        logger.debug(f"Cache hit: {key}")
    
    def track_cache_miss(self, key: str):
        """Track a cache miss."""
        self.stats["cache_misses"] += 1
        logger.debug(f"Cache miss: {key}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get middleware statistics."""
        total_cache_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
        cache_hit_rate = (
            self.stats["cache_hits"] / total_cache_requests
            if total_cache_requests > 0 else 0.0
        )
        
        return {
            **self.stats,
            "cache_hit_rate": cache_hit_rate,
            "total_cache_requests": total_cache_requests
        }
    
    def reset_stats(self):
        """Reset statistics."""
        self.stats = {
            "queries_analyzed": 0,
            "context_fetches": 0,
            "prompt_enrichments": 0,
            "resource_accesses": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }


# Global middleware instance
_middleware = ContextMiddleware()


def get_middleware() -> ContextMiddleware:
    """Get the global middleware instance."""
    return _middleware


def with_context_tracking(func: Callable) -> Callable:
    """
    Decorator to track context usage in functions.
    
    Args:
        func: Function to wrap
    
    Returns:
        Wrapped function with context tracking
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug(f"{func.__name__} executed in {duration:.2f}s")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed: {str(e)}")
            raise
    
    return wrapper

