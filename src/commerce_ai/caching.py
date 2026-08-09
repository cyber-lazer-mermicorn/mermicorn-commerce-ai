"""
Caching — Redis with In-Memory Fallback
=========================================
Transparent caching layer with TTL and invalidation.
"""

import os
import time
import json
import hashlib
from typing import Any, Optional
from collections import OrderedDict
import threading


class MemoryCache:
    """LRU in-memory cache with TTL."""
    
    def __init__(self, max_size: int = 1000):
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._max_size = max_size
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if expiry > time.time():
                    self._cache.move_to_end(key)
                    self.hits += 1
                    return value
                else:
                    del self._cache[key]
            self.misses += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            elif len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
            self._cache[key] = (value, time.time() + ttl)
    
    def delete(self, key: str):
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self):
        with self._lock:
            self._cache.clear()
    
    def stats(self) -> dict:
        total = self.hits + self.misses
        return {
            "size": len(self._cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{(self.hits/total*100):.1f}%" if total else "0%",
        }


class RedisCache:
    """Redis cache wrapper."""
    
    def __init__(self):
        self.url = os.environ.get("REDIS_URL", "")
        self._client = None
        if self.url:
            try:
                import redis
                self._client = redis.from_url(self.url, decode_responses=True)
            except ImportError:
                pass
    
    def is_available(self) -> bool:
        if not self._client:
            return False
        try:
            self._client.ping()
            return True
        except Exception:
            return False
    
    def get(self, key: str) -> Optional[Any]:
        if not self.is_available():
            return None
        try:
            val = self._client.get(key)
            return json.loads(val) if val else None
        except Exception:
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        if not self.is_available():
            return
        try:
            self._client.setex(key, ttl, json.dumps(value))
        except Exception:
            pass
    
    def delete(self, key: str):
        if self.is_available():
            try:
                self._client.delete(key)
            except Exception:
                pass
    
    def clear(self):
        if self.is_available():
            try:
                self._client.flushdb()
            except Exception:
                pass


class Cache:
    """Multi-tier cache: Redis → Memory."""
    
    def __init__(self):
        self.redis = RedisCache()
        self.memory = MemoryCache()
    
    def get(self, key: str) -> Optional[Any]:
        # Try memory first
        val = self.memory.get(key)
        if val is not None:
            return val
        # Try Redis
        val = self.redis.get(key)
        if val is not None:
            self.memory.set(key, val, ttl=60)
            return val
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        self.memory.set(key, value, ttl)
        self.redis.set(key, value, ttl)
    
    def delete(self, key: str):
        self.memory.delete(key)
        self.redis.delete(key)
    
    def clear(self):
        self.memory.clear()
        self.redis.clear()
    
    def stats(self) -> dict:
        return {
            "memory": self.memory.stats(),
            "redis": "connected" if self.redis.is_available() else "disconnected",
        }


cache = Cache()
