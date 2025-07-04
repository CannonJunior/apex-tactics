"""
Advanced Cache Management System

Intelligent caching for expensive operations in the tactical RPG engine.
Supports multiple cache strategies, automatic invalidation, and smart eviction.
"""

import time
import threading
import weakref
from typing import Any, Dict, List, Optional, Callable, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import OrderedDict, defaultdict
import hashlib
import pickle
import functools


class CacheStrategy(Enum):
    """Cache eviction strategies."""
    LRU = "lru"           # Least Recently Used
    LFU = "lfu"           # Least Frequently Used
    TTL = "ttl"           # Time To Live
    FIFO = "fifo"         # First In First Out
    ADAPTIVE = "adaptive"  # Adaptive based on access patterns


@dataclass
class CacheEntry:
    """Single cache entry with metadata."""
    key: str
    value: Any
    created_time: float
    last_accessed: float
    access_count: int = 0
    size_bytes: int = 0
    ttl: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)
    
    @property
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.ttl is None:
            return False
        return time.time() - self.created_time > self.ttl
    
    @property
    def age(self) -> float:
        """Age of entry in seconds."""
        return time.time() - self.created_time


@dataclass
class CacheStats:
    """Cache statistics for monitoring."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    invalidations: int = 0
    memory_used: int = 0
    total_entries: int = 0
    
    @property
    def hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class CacheManager:
    """
    Advanced cache manager with multiple strategies and intelligent features.
    
    Features:
    - Multiple eviction strategies
    - TTL support with automatic cleanup
    - Dependency tracking and invalidation
    - Memory usage monitoring
    - Thread-safe operations
    - Cache warming and preloading
    - Performance statistics
    """
    
    def __init__(self, 
                 strategy: CacheStrategy = CacheStrategy.LRU,
                 max_size: int = 1000,
                 max_memory_mb: int = 100,
                 default_ttl: Optional[float] = None):
        self.strategy = strategy
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.default_ttl = default_ttl
        
        # Storage
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: OrderedDict = OrderedDict()  # For LRU
        self.access_frequency: Dict[str, int] = defaultdict(int)  # For LFU
        
        # Dependency tracking
        self.dependencies: Dict[str, List[str]] = defaultdict(list)  # key -> dependents
        self.dependents: Dict[str, List[str]] = defaultdict(list)   # key -> dependencies
        
        # Statistics
        self.stats = CacheStats()
        self.lock = threading.RLock()
        
        # Background cleanup
        self._cleanup_thread = None
        self._stop_cleanup = False
        self._start_cleanup_thread()
        
        print(f"💾 Cache Manager initialized ({strategy.value}, max_size={max_size})")
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread for expired entries."""
        def cleanup_loop():
            while not self._stop_cleanup:
                try:
                    self._cleanup_expired()
                    time.sleep(30)  # Cleanup every 30 seconds
                except Exception as e:
                    print(f"Cache cleanup error: {e}")
        
        self._cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self._cleanup_thread.start()
    
    def _cleanup_expired(self):
        """Remove expired entries."""
        with self.lock:
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.is_expired
            ]
            
            for key in expired_keys:
                self._remove_entry(key)
                self.stats.evictions += 1
    
    def _calculate_size(self, value: Any) -> int:
        """Estimate memory size of value."""
        try:
            return len(pickle.dumps(value))
        except:
            # Fallback for non-pickleable objects
            return 64  # Rough estimate
    
    def _generate_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """Generate cache key for function call."""
        # Create a hashable representation
        key_data = {
            'func': f"{func.__module__}.{func.__name__}",
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        
        # Use hash for compact key
        key_str = str(key_data)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _update_access_tracking(self, key: str):
        """Update access tracking for different strategies."""
        entry = self.cache[key]
        entry.last_accessed = time.time()
        entry.access_count += 1
        
        # Update strategy-specific tracking
        if self.strategy == CacheStrategy.LRU:
            # Move to end (most recently used)
            self.access_order.move_to_end(key)
        elif self.strategy == CacheStrategy.LFU:
            self.access_frequency[key] += 1
    
    def _should_evict(self) -> bool:
        """Check if eviction is needed."""
        return (len(self.cache) >= self.max_size or 
                self.stats.memory_used >= self.max_memory_bytes)
    
    def _select_eviction_key(self) -> Optional[str]:
        """Select key for eviction based on strategy."""
        if not self.cache:
            return None
        
        if self.strategy == CacheStrategy.LRU:
            # Remove least recently used (first in access_order)
            return next(iter(self.access_order))
        
        elif self.strategy == CacheStrategy.LFU:
            # Remove least frequently used
            return min(self.cache.keys(), 
                      key=lambda k: self.access_frequency[k])
        
        elif self.strategy == CacheStrategy.FIFO:
            # Remove oldest entry
            return min(self.cache.keys(), 
                      key=lambda k: self.cache[k].created_time)
        
        elif self.strategy == CacheStrategy.TTL:
            # Remove entry closest to expiration
            return min(self.cache.keys(), 
                      key=lambda k: self.cache[k].created_time + (self.cache[k].ttl or float('inf')))
        
        elif self.strategy == CacheStrategy.ADAPTIVE:
            # Adaptive strategy based on access patterns
            return self._adaptive_eviction_key()
        
        return next(iter(self.cache))  # Fallback
    
    def _adaptive_eviction_key(self) -> str:
        """Adaptive eviction based on access patterns."""
        current_time = time.time()
        
        # Score entries based on recency, frequency, and size
        scored_keys = []
        
        for key, entry in self.cache.items():
            recency_score = 1.0 / (current_time - entry.last_accessed + 1)
            frequency_score = entry.access_count / max(entry.age, 1)
            size_penalty = entry.size_bytes / (1024 * 1024)  # MB penalty
            
            # Combined score (higher is better)
            score = recency_score + frequency_score - size_penalty
            scored_keys.append((score, key))
        
        # Return key with lowest score
        return min(scored_keys)[1]
    
    def _remove_entry(self, key: str):
        """Remove entry and clean up tracking."""
        if key not in self.cache:
            return
        
        entry = self.cache[key]
        self.stats.memory_used -= entry.size_bytes
        self.stats.total_entries -= 1
        
        # Clean up tracking
        del self.cache[key]
        self.access_order.pop(key, None)
        self.access_frequency.pop(key, None)
        
        # Clean up dependencies
        self._remove_dependencies(key)
    
    def _remove_dependencies(self, key: str):
        """Remove dependency tracking for a key."""
        # Remove from dependents
        for dep_key in self.dependents[key]:
            if key in self.dependencies[dep_key]:
                self.dependencies[dep_key].remove(key)
        del self.dependents[key]
        
        # Remove from dependencies
        for dependent in self.dependencies[key]:
            if key in self.dependents[dependent]:
                self.dependents[dependent].remove(key)
        del self.dependencies[key]
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self.lock:
            if key not in self.cache:
                self.stats.misses += 1
                return None
            
            entry = self.cache[key]
            
            # Check expiration
            if entry.is_expired:
                self._remove_entry(key)
                self.stats.misses += 1
                return None
            
            # Update access tracking
            self._update_access_tracking(key)
            self.stats.hits += 1
            
            return entry.value
    
    def put(self, key: str, value: Any, 
           ttl: Optional[float] = None,
           dependencies: Optional[List[str]] = None) -> bool:
        """
        Put value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live (overrides default)
            dependencies: List of keys this entry depends on
            
        Returns:
            True if successfully cached
        """
        with self.lock:
            # Check if eviction is needed
            while self._should_evict():
                evict_key = self._select_eviction_key()
                if evict_key:
                    self._remove_entry(evict_key)
                    self.stats.evictions += 1
                else:
                    break
            
            # Calculate size
            size_bytes = self._calculate_size(value)
            
            # Create entry
            current_time = time.time()
            entry = CacheEntry(
                key=key,
                value=value,
                created_time=current_time,
                last_accessed=current_time,
                size_bytes=size_bytes,
                ttl=ttl or self.default_ttl,
                dependencies=dependencies or []
            )
            
            # Remove existing entry if present
            if key in self.cache:
                self._remove_entry(key)
            
            # Add new entry
            self.cache[key] = entry
            self.access_order[key] = True
            self.stats.memory_used += size_bytes
            self.stats.total_entries += 1
            
            # Set up dependencies
            if dependencies:
                self.dependents[key] = dependencies.copy()
                for dep_key in dependencies:
                    self.dependencies[dep_key].append(key)
            
            return True
    
    def invalidate(self, key: str) -> bool:
        """
        Invalidate cache entry and all dependents.
        
        Args:
            key: Key to invalidate
            
        Returns:
            True if key was found and invalidated
        """
        with self.lock:
            if key not in self.cache:
                return False
            
            # Collect all dependents recursively
            to_invalidate = {key}
            queue = [key]
            
            while queue:
                current_key = queue.pop(0)
                for dependent in self.dependencies[current_key]:
                    if dependent not in to_invalidate:
                        to_invalidate.add(dependent)
                        queue.append(dependent)
            
            # Remove all collected keys
            for invalid_key in to_invalidate:
                if invalid_key in self.cache:
                    self._remove_entry(invalid_key)
                    self.stats.invalidations += 1
            
            return True
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern.
        
        Args:
            pattern: String pattern to match (simple substring match)
            
        Returns:
            Number of entries invalidated
        """
        with self.lock:
            matching_keys = [
                key for key in self.cache.keys()
                if pattern in key
            ]
            
            count = 0
            for key in matching_keys:
                if self.invalidate(key):
                    count += 1
            
            return count
    
    def warm_cache(self, func: Callable, param_sets: List[Tuple[tuple, dict]]):
        """
        Warm cache by pre-computing function results.
        
        Args:
            func: Function to cache
            param_sets: List of (args, kwargs) tuples to pre-compute
        """
        print(f"🔥 Warming cache for {func.__name__} with {len(param_sets)} parameter sets")
        
        warmed = 0
        for args, kwargs in param_sets:
            try:
                key = self._generate_key(func, args, kwargs)
                if key not in self.cache:
                    result = func(*args, **kwargs)
                    self.put(key, result)
                    warmed += 1
            except Exception as e:
                print(f"Cache warming failed for {args}, {kwargs}: {e}")
        
        print(f"🔥 Cache warmed: {warmed}/{len(param_sets)} entries")
    
    def cached_function(self, 
                       ttl: Optional[float] = None,
                       dependencies: Optional[List[str]] = None):
        """
        Decorator for caching function results.
        
        Args:
            ttl: Time to live for cached results
            dependencies: Static dependencies for all calls
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                key = self._generate_key(func, args, kwargs)
                
                # Try to get from cache
                result = self.get(key)
                if result is not None:
                    return result
                
                # Compute result
                result = func(*args, **kwargs)
                
                # Cache result
                self.put(key, result, ttl=ttl, dependencies=dependencies)
                
                return result
            
            # Add cache control methods to function
            wrapper.cache_invalidate = lambda *args, **kwargs: self.invalidate(
                self._generate_key(func, args, kwargs)
            )
            wrapper.cache_clear = lambda: self.invalidate_pattern(func.__name__)
            
            return wrapper
        return decorator
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self.lock:
            return CacheStats(
                hits=self.stats.hits,
                misses=self.stats.misses,
                evictions=self.stats.evictions,
                invalidations=self.stats.invalidations,
                memory_used=self.stats.memory_used,
                total_entries=len(self.cache)
            )
    
    def clear(self):
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            self.access_order.clear()
            self.access_frequency.clear()
            self.dependencies.clear()
            self.dependents.clear()
            self.stats = CacheStats()
        
        print("💾 Cache cleared")
    
    def shutdown(self):
        """Shutdown cache manager."""
        self._stop_cleanup = True
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=1.0)
        self.clear()
        print("💾 Cache Manager shut down")


# Global cache instances for different purposes
stat_cache = CacheManager(
    strategy=CacheStrategy.LRU,
    max_size=5000,
    max_memory_mb=50,
    default_ttl=60.0  # Stats valid for 1 minute
)

action_cache = CacheManager(
    strategy=CacheStrategy.ADAPTIVE,
    max_size=2000,
    max_memory_mb=30,
    default_ttl=None  # Actions cached until invalidated
)

ui_cache = CacheManager(
    strategy=CacheStrategy.TTL,
    max_size=1000,
    max_memory_mb=20,
    default_ttl=5.0  # UI data cached for 5 seconds
)


# Convenience decorators
def cache_stats(ttl: float = 60.0):
    """Cache stat calculations."""
    return stat_cache.cached_function(ttl=ttl)


def cache_action_result(dependencies: Optional[List[str]] = None):
    """Cache action results."""
    return action_cache.cached_function(dependencies=dependencies)


def cache_ui_data(ttl: float = 5.0):
    """Cache UI data."""
    return ui_cache.cached_function(ttl=ttl)