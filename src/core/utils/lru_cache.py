"""
LRU Cache Implementation

Simple Least Recently Used cache for performance optimization.
"""

from typing import Dict, Any, Optional, Tuple
from collections import OrderedDict


class LRUCache:
    """
    Least Recently Used cache implementation.
    
    Provides O(1) access and eviction using OrderedDict.
    Thread-safe for single-threaded environments.
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of items to cache
        """
        self.max_size = max_size
        self._cache: OrderedDict = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def get(self, key: Any) -> Optional[Any]:
        """
        Get value by key, marking it as recently used.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if key in self._cache:
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]
        
        self._misses += 1
        return None
    
    def put(self, key: Any, value: Any) -> None:
        """
        Put value in cache with given key.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        if key in self._cache:
            # Update existing key
            self._cache[key] = value
            self._cache.move_to_end(key)
        else:
            # Add new key
            if len(self._cache) >= self.max_size:
                # Remove least recently used item
                self._cache.popitem(last=False)
                self._evictions += 1
            
            self._cache[key] = value
    
    def remove(self, key: Any) -> bool:
        """
        Remove item from cache.
        
        Args:
            key: Cache key to remove
            
        Returns:
            True if item was removed, False if not found
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cached items"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def size(self) -> int:
        """Get current number of cached items"""
        return len(self._cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
        
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'hits': self._hits,
            'misses': self._misses,
            'evictions': self._evictions,
            'hit_rate': hit_rate,
            'total_requests': total_requests
        }
    
    def get_usage_ratio(self) -> float:
        """Get cache usage ratio (0.0 to 1.0)"""
        return len(self._cache) / self.max_size if self.max_size > 0 else 0.0
    
    def is_full(self) -> bool:
        """Check if cache is at maximum capacity"""
        return len(self._cache) >= self.max_size
    
    def keys(self):
        """Get all cache keys"""
        return self._cache.keys()
    
    def values(self):
        """Get all cache values"""
        return self._cache.values()
    
    def items(self):
        """Get all cache items"""
        return self._cache.items()
    
    def __contains__(self, key: Any) -> bool:
        """Check if key exists in cache"""
        return key in self._cache
    
    def __len__(self) -> int:
        """Get number of cached items"""
        return len(self._cache)
    
    def __str__(self) -> str:
        stats = self.get_stats()
        return f"LRUCache(size={stats['size']}/{stats['max_size']}, hit_rate={stats['hit_rate']:.2%})"
    
    def __repr__(self) -> str:
        return self.__str__()