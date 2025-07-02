"""
AI Performance Optimizer

Implements performance optimizations for AI decision-making processes,
including caching, parallel processing, and computational efficiency improvements.
"""

import asyncio
import time
import hashlib
import pickle
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict
from dataclasses import dataclass, field
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

import structlog
import numpy as np
from pydantic import BaseModel

from .models import AIDecisionRequest, AIDecisionResponse, BattlefieldState

logger = structlog.get_logger()


class OptimizationType(str, Enum):
    """Types of performance optimizations"""
    CACHING = "caching"
    PARALLEL_PROCESSING = "parallel_processing"
    MEMOIZATION = "memoization"
    LAZY_EVALUATION = "lazy_evaluation"
    PRUNING = "pruning"
    BATCH_PROCESSING = "batch_processing"


class CacheStrategy(str, Enum):
    """Cache eviction strategies"""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    FIFO = "fifo"  # First In First Out


@dataclass
class PerformanceMetrics:
    """Performance tracking metrics"""
    decision_count: int = 0
    total_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    parallel_executions: int = 0
    average_decision_time: float = 0.0
    peak_memory_usage: float = 0.0
    optimization_savings: float = 0.0


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    timestamp: datetime
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    computation_time: float = 0.0


class LRUCache:
    """Least Recently Used cache implementation"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                return entry.value
            return None
    
    def put(self, key: str, value: Any, computation_time: float = 0.0):
        """Put value in cache"""
        with self.lock:
            if key in self.cache:
                # Update existing entry
                entry = self.cache[key]
                entry.value = value
                entry.last_accessed = datetime.now()
                entry.access_count += 1
                entry.computation_time = computation_time
                self.cache.move_to_end(key)
            else:
                # Add new entry
                if len(self.cache) >= self.max_size:
                    # Remove least recently used
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                
                entry = CacheEntry(
                    key=key,
                    value=value,
                    timestamp=datetime.now(),
                    computation_time=computation_time
                )
                self.cache[key] = entry
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_access = sum(entry.access_count for entry in self.cache.values())
            total_time_saved = sum(entry.computation_time * (entry.access_count - 1) 
                                 for entry in self.cache.values())
            
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "total_accesses": total_access,
                "time_saved_seconds": total_time_saved,
                "oldest_entry": min(self.cache.values(), key=lambda e: e.timestamp).timestamp if self.cache else None
            }


class DecisionCache:
    """Specialized cache for AI decisions"""
    
    def __init__(self, max_size: int = 500, ttl_seconds: int = 300):
        self.cache = LRUCache(max_size)
        self.ttl_seconds = ttl_seconds
        self.similarity_threshold = 0.9
    
    def _generate_cache_key(self, request: AIDecisionRequest, battlefield_state: BattlefieldState) -> str:
        """Generate cache key for decision request"""
        # Create simplified state representation for caching
        state_data = {
            "unit_positions": [(u.id, u.position.x, u.position.y, u.team) for u in battlefield_state.units if u.alive],
            "unit_health": [(u.id, u.current_hp) for u in battlefield_state.units if u.alive],
            "difficulty": request.difficulty_level,
            "constraints": request.constraints or {}
        }
        
        # Hash the state data
        state_str = str(sorted(state_data.items()))
        return hashlib.md5(state_str.encode()).hexdigest()
    
    def get_cached_decision(self, request: AIDecisionRequest, battlefield_state: BattlefieldState) -> Optional[AIDecisionResponse]:
        """Get cached decision if available and valid"""
        cache_key = self._generate_cache_key(request, battlefield_state)
        
        cached_entry = self.cache.get(cache_key)
        if cached_entry:
            # Check TTL
            if datetime.now() - cached_entry.last_accessed < timedelta(seconds=self.ttl_seconds):
                logger.debug("Cache hit for AI decision", key=cache_key)
                return cached_entry
            else:
                logger.debug("Cache entry expired", key=cache_key)
        
        return None
    
    def cache_decision(self, request: AIDecisionRequest, battlefield_state: BattlefieldState, 
                      response: AIDecisionResponse, computation_time: float):
        """Cache decision response"""
        cache_key = self._generate_cache_key(request, battlefield_state)
        self.cache.put(cache_key, response, computation_time)
        logger.debug("Cached AI decision", key=cache_key, computation_time=computation_time)


class ParallelProcessor:
    """Parallel processing for AI computations"""
    
    def __init__(self, max_workers: int = 4):
        self.thread_executor = ThreadPoolExecutor(max_workers=max_workers)
        self.process_executor = ProcessPoolExecutor(max_workers=min(max_workers, 2))
        self.max_workers = max_workers
    
    async def process_parallel_decisions(self, decision_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple decisions in parallel"""
        if len(decision_requests) <= 1:
            return decision_requests
        
        # Split requests into batches
        batch_size = max(1, len(decision_requests) // self.max_workers)
        batches = [decision_requests[i:i + batch_size] for i in range(0, len(decision_requests), batch_size)]
        
        # Process batches in parallel
        loop = asyncio.get_event_loop()
        tasks = []
        
        for batch in batches:
            task = loop.run_in_executor(self.thread_executor, self._process_batch, batch)
            tasks.append(task)
        
        batch_results = await asyncio.gather(*tasks)
        
        # Flatten results
        results = []
        for batch_result in batch_results:
            results.extend(batch_result)
        
        return results
    
    def _process_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a batch of decisions"""
        # Placeholder for batch processing logic
        # In a real implementation, this would contain the actual AI processing
        results = []
        for request in batch:
            # Simulate processing
            time.sleep(0.01)  # Simulate computation
            result = {"processed": True, "request_id": request.get("id")}
            results.append(result)
        
        return results
    
    async def parallel_evaluation(self, candidates: List[Any], eval_func: Callable) -> List[Tuple[Any, float]]:
        """Evaluate multiple candidates in parallel"""
        loop = asyncio.get_event_loop()
        
        # Create evaluation tasks
        tasks = []
        for candidate in candidates:
            task = loop.run_in_executor(self.thread_executor, eval_func, candidate)
            tasks.append(task)
        
        # Execute all evaluations in parallel
        scores = await asyncio.gather(*tasks)
        
        return list(zip(candidates, scores))
    
    def shutdown(self):
        """Shutdown executors"""
        self.thread_executor.shutdown(wait=True)
        self.process_executor.shutdown(wait=True)


class ComputationOptimizer:
    """Optimizes computational complexity of AI algorithms"""
    
    def __init__(self):
        self.memoization_cache = {}
        self.pruning_enabled = True
        self.early_termination_threshold = 0.95
    
    def memoize(self, func: Callable) -> Callable:
        """Decorator for function memoization"""
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
            
            if key in self.memoization_cache:
                return self.memoization_cache[key]
            
            result = func(*args, **kwargs)
            self.memoization_cache[key] = result
            return result
        
        return wrapper
    
    def prune_search_space(self, candidates: List[Any], eval_func: Callable, max_candidates: int = 10) -> List[Any]:
        """Prune search space by keeping only top candidates"""
        if not self.pruning_enabled or len(candidates) <= max_candidates:
            return candidates
        
        # Quick evaluation for pruning
        scored_candidates = [(candidate, eval_func(candidate)) for candidate in candidates]
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        return [candidate for candidate, score in scored_candidates[:max_candidates]]
    
    def early_termination_check(self, current_best_score: float, iteration: int, max_iterations: int) -> bool:
        """Check if search can terminate early"""
        if current_best_score >= self.early_termination_threshold:
            return True
        
        # Terminate if we've done enough iterations and have a decent score
        if iteration > max_iterations * 0.7 and current_best_score > 0.8:
            return True
        
        return False
    
    def clear_memoization_cache(self):
        """Clear memoization cache"""
        self.memoization_cache.clear()


class BatchProcessor:
    """Batch processing for improved efficiency"""
    
    def __init__(self, batch_size: int = 10, max_wait_time: float = 0.1):
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.pending_requests: List[Dict[str, Any]] = []
        self.pending_futures: List[asyncio.Future] = []
        self.last_batch_time = time.time()
        self.processing_lock = asyncio.Lock()
    
    async def add_request(self, request: Dict[str, Any]) -> Any:
        """Add request to batch processing queue"""
        async with self.processing_lock:
            future = asyncio.Future()
            self.pending_requests.append(request)
            self.pending_futures.append(future)
            
            # Check if we should process batch now
            should_process = (
                len(self.pending_requests) >= self.batch_size or
                time.time() - self.last_batch_time > self.max_wait_time
            )
            
            if should_process:
                await self._process_batch()
        
        return await future
    
    async def _process_batch(self):
        """Process current batch of requests"""
        if not self.pending_requests:
            return
        
        requests = self.pending_requests.copy()
        futures = self.pending_futures.copy()
        
        self.pending_requests.clear()
        self.pending_futures.clear()
        self.last_batch_time = time.time()
        
        try:
            # Process all requests in the batch
            results = await self._batch_process_requests(requests)
            
            # Resolve futures with results
            for future, result in zip(futures, results):
                if not future.done():
                    future.set_result(result)
                    
        except Exception as e:
            # Set exception for all futures
            for future in futures:
                if not future.done():
                    future.set_exception(e)
    
    async def _batch_process_requests(self, requests: List[Dict[str, Any]]) -> List[Any]:
        """Process batch of requests - override in subclasses"""
        # Placeholder implementation
        return [{"processed": True, "id": req.get("id")} for req in requests]


class PerformanceOptimizer:
    """Main performance optimization system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        # Initialize optimization components
        self.decision_cache = DecisionCache(
            max_size=config.get("cache_size", 500),
            ttl_seconds=config.get("cache_ttl", 300)
        )
        
        self.parallel_processor = ParallelProcessor(
            max_workers=config.get("max_workers", 4)
        )
        
        self.computation_optimizer = ComputationOptimizer()
        self.batch_processor = BatchProcessor(
            batch_size=config.get("batch_size", 10),
            max_wait_time=config.get("max_wait_time", 0.1)
        )
        
        # Performance tracking
        self.metrics = PerformanceMetrics()
        self.optimization_history: List[Dict[str, Any]] = []
        
        # Configuration
        self.optimization_enabled = config.get("enabled", True)
        self.optimization_types = set(config.get("types", [
            OptimizationType.CACHING,
            OptimizationType.PARALLEL_PROCESSING,
            OptimizationType.MEMOIZATION
        ]))
    
    async def optimize_decision(self, request: AIDecisionRequest, battlefield_state: BattlefieldState, 
                              decision_func: Callable) -> Tuple[AIDecisionResponse, Dict[str, Any]]:
        """Optimize AI decision process"""
        start_time = time.time()
        optimization_info = {"optimizations_used": []}
        
        # Try cache first
        if OptimizationType.CACHING in self.optimization_types:
            cached_decision = self.decision_cache.get_cached_decision(request, battlefield_state)
            if cached_decision:
                self.metrics.cache_hits += 1
                optimization_info["optimizations_used"].append("cache_hit")
                optimization_info["cache_hit"] = True
                optimization_info["computation_time"] = 0.0
                return cached_decision, optimization_info
        
        self.metrics.cache_misses += 1
        
        # Apply computational optimizations
        optimized_decision_func = decision_func
        if OptimizationType.MEMOIZATION in self.optimization_types:
            optimized_decision_func = self.computation_optimizer.memoize(decision_func)
            optimization_info["optimizations_used"].append("memoization")
        
        # Execute decision with optimizations
        try:
            decision_response = await optimized_decision_func(request, battlefield_state)
        except Exception as e:
            logger.error("Optimized decision execution failed", error=str(e))
            raise
        
        computation_time = time.time() - start_time
        
        # Cache the result
        if OptimizationType.CACHING in self.optimization_types:
            self.decision_cache.cache_decision(request, battlefield_state, decision_response, computation_time)
            optimization_info["optimizations_used"].append("caching")
        
        # Update metrics
        self.metrics.decision_count += 1
        self.metrics.total_time += computation_time
        self.metrics.average_decision_time = self.metrics.total_time / self.metrics.decision_count
        
        optimization_info.update({
            "cache_hit": False,
            "computation_time": computation_time,
            "total_decisions": self.metrics.decision_count
        })
        
        return decision_response, optimization_info
    
    async def optimize_batch_decisions(self, requests: List[Tuple[AIDecisionRequest, BattlefieldState]], 
                                     decision_func: Callable) -> List[Tuple[AIDecisionResponse, Dict[str, Any]]]:
        """Optimize batch decision processing"""
        if not requests or OptimizationType.BATCH_PROCESSING not in self.optimization_types:
            # Process individually
            results = []
            for request, battlefield_state in requests:
                result = await self.optimize_decision(request, battlefield_state, decision_func)
                results.append(result)
            return results
        
        # Batch processing
        start_time = time.time()
        results = []
        
        # Separate cached and non-cached requests
        cached_results = []
        non_cached_requests = []
        
        for i, (request, battlefield_state) in enumerate(requests):
            if OptimizationType.CACHING in self.optimization_types:
                cached_decision = self.decision_cache.get_cached_decision(request, battlefield_state)
                if cached_decision:
                    cached_results.append((i, cached_decision, {"cache_hit": True, "computation_time": 0.0}))
                    continue
            
            non_cached_requests.append((i, request, battlefield_state))
        
        # Process non-cached requests in parallel if enabled
        if non_cached_requests and OptimizationType.PARALLEL_PROCESSING in self.optimization_types:
            # Process in parallel
            async def process_single(idx_req_state):
                idx, req, state = idx_req_state
                decision = await decision_func(req, state)
                return idx, decision, {"cache_hit": False, "computation_time": time.time() - start_time}
            
            non_cached_results = await asyncio.gather(*[
                process_single(item) for item in non_cached_requests
            ])
        else:
            # Process sequentially
            non_cached_results = []
            for idx, request, battlefield_state in non_cached_requests:
                decision = await decision_func(request, battlefield_state)
                non_cached_results.append((idx, decision, {"cache_hit": False, "computation_time": time.time() - start_time}))
        
        # Combine results in original order
        all_results = cached_results + non_cached_results
        all_results.sort(key=lambda x: x[0])  # Sort by original index
        
        # Cache non-cached results
        for idx, decision, info in non_cached_results:
            if OptimizationType.CACHING in self.optimization_types:
                original_request, original_state = requests[idx]
                self.decision_cache.cache_decision(original_request, original_state, decision, info["computation_time"])
        
        # Update metrics
        batch_time = time.time() - start_time
        self.metrics.decision_count += len(requests)
        self.metrics.total_time += batch_time
        self.metrics.parallel_executions += 1
        self.metrics.cache_hits += len(cached_results)
        self.metrics.cache_misses += len(non_cached_results)
        
        return [(result[1], result[2]) for result in all_results]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        cache_stats = self.decision_cache.cache.get_stats()
        
        cache_hit_rate = 0.0
        if self.metrics.cache_hits + self.metrics.cache_misses > 0:
            cache_hit_rate = self.metrics.cache_hits / (self.metrics.cache_hits + self.metrics.cache_misses)
        
        return {
            "decisions_processed": self.metrics.decision_count,
            "total_processing_time": self.metrics.total_time,
            "average_decision_time": self.metrics.average_decision_time,
            "cache_hit_rate": cache_hit_rate,
            "cache_hits": self.metrics.cache_hits,
            "cache_misses": self.metrics.cache_misses,
            "parallel_executions": self.metrics.parallel_executions,
            "optimization_savings": self.metrics.optimization_savings,
            "cache_stats": cache_stats,
            "optimizations_enabled": list(self.optimization_types),
            "optimization_history_size": len(self.optimization_history)
        }
    
    def configure_optimization(self, optimization_type: OptimizationType, enabled: bool):
        """Enable or disable specific optimization"""
        if enabled:
            self.optimization_types.add(optimization_type)
        else:
            self.optimization_types.discard(optimization_type)
        
        logger.info("Optimization configuration changed", 
                   optimization=optimization_type, 
                   enabled=enabled)
    
    def clear_caches(self):
        """Clear all caches"""
        self.decision_cache.cache.clear()
        self.computation_optimizer.clear_memoization_cache()
        logger.info("All caches cleared")
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.metrics = PerformanceMetrics()
        self.optimization_history.clear()
        logger.info("Performance metrics reset")
    
    async def shutdown(self):
        """Shutdown optimizer and clean up resources"""
        self.parallel_processor.shutdown()
        self.clear_caches()
        logger.info("Performance optimizer shutdown complete")
    
    def analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        if len(self.optimization_history) < 2:
            return {"status": "insufficient_data"}
        
        # Calculate trends
        recent_decisions = self.optimization_history[-100:]  # Last 100 decisions
        older_decisions = self.optimization_history[-200:-100] if len(self.optimization_history) >= 200 else []
        
        if not older_decisions:
            return {"status": "insufficient_historical_data"}
        
        recent_avg_time = np.mean([d["computation_time"] for d in recent_decisions])
        older_avg_time = np.mean([d["computation_time"] for d in older_decisions])
        
        performance_improvement = (older_avg_time - recent_avg_time) / older_avg_time if older_avg_time > 0 else 0
        
        recent_cache_rate = np.mean([d.get("cache_hit", False) for d in recent_decisions])
        older_cache_rate = np.mean([d.get("cache_hit", False) for d in older_decisions])
        
        return {
            "status": "analysis_complete",
            "performance_improvement": performance_improvement,
            "recent_avg_time": recent_avg_time,
            "older_avg_time": older_avg_time,
            "recent_cache_hit_rate": recent_cache_rate,
            "older_cache_hit_rate": older_cache_rate,
            "cache_improvement": recent_cache_rate - older_cache_rate,
            "decisions_analyzed": len(recent_decisions) + len(older_decisions)
        }