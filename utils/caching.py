import functools
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SimpleCache:
    """Simple in-memory cache with TTL"""
    
    def __init__(self):
        self.cache = {}
        self.timestamps = {}
    
    def get(self, key):
        if key in self.cache:
            # Check if expired
            if datetime.now() - self.timestamps[key] < timedelta(hours=1):
                return self.cache[key]
            else:
                # Expired, remove
                del self.cache[key]
                del self.timestamps[key]
        return None
    
    def set(self, key, value):
        self.cache[key] = value
        self.timestamps[key] = datetime.now()
    
    def clear(self):
        self.cache.clear()
        self.timestamps.clear()

# Global cache instance
cache = SimpleCache()

def cached(ttl_hours=1):
    """Decorator for caching function results"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            # Note: args and kwargs must be hashable or stringifiable
            try:
                cache_key = f"{func.__name__}_{str(args)}_{str(kwargs)}"
                
                # Check cache
                result = cache.get(cache_key)
                if result is not None:
                    return result
                
                # Compute and cache
                result = func(*args, **kwargs)
                cache.set(cache_key, result)
                return result
            except Exception as e:
                # Fallback if caching fails (e.g. unhashable args)
                logger.warning(f"Caching failed for {func.__name__}: {e}")
                return func(*args, **kwargs)
        
        return wrapper
    return decorator
