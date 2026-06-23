"""
In-Memory Cache with TTL
A lightweight caching solution that works without Redis.
Perfect for Render free tier deployment.
"""

import time
from typing import Any, Optional, Dict
from functools import wraps
import hashlib
import json

class InMemoryCache:
    def __init__(self, default_ttl: int = 300):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl  # 5 minutes default
        
    def _is_expired(self, key: str) -> bool:
        if key not in self._cache:
            return True
        return time.time() > self._cache[key]["expires_at"]
    
    def get(self, key: str) -> Optional[Any]:
        if self._is_expired(key):
            self.delete(key)
            return None
        return self._cache[key]["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        expires_at = time.time() + (ttl or self.default_ttl)
        self._cache[key] = {
            "value": value,
            "expires_at": expires_at
        }
        
    def delete(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]
            
    def clear(self) -> None:
        self._cache.clear()
        
    def cleanup_expired(self) -> int:
        """Remove all expired entries. Returns count of removed items."""
        expired_keys = [k for k in self._cache if self._is_expired(k)]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)
    
    def stats(self) -> Dict[str, Any]:
        return {
            "total_keys": len(self._cache),
            "memory_estimate_kb": len(json.dumps(self._cache, default=str)) / 1024
        }

# Global cache instance
cache = InMemoryCache(default_ttl=300)

def cache_key(*args, **kwargs) -> str:
    """Generate a cache key from arguments."""
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()

def cached(ttl: int = 300):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{cache_key(*args, **kwargs)}"
            result = cache.get(key)
            if result is not None:
                print(f"Cache HIT: {key[:50]}...")
                return result
            print(f"Cache MISS: {key[:50]}...")
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result
        return wrapper
    return decorator

if __name__ == "__main__":
    # Test the cache
    cache.set("test_key", {"data": "hello"}, ttl=5)
    print("Get immediately:", cache.get("test_key"))
    print("Cache stats:", cache.stats())
