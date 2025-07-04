"""
Parallel Execution System

High-performance parallel processing for CPU-intensive operations
in the tactical RPG engine, including action execution, AI decisions,
and batch processing.
"""

import asyncio
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import time
import queue
import functools
from contextlib import contextmanager


class ExecutionMode(Enum):
    """Parallel execution modes."""
    SEQUENTIAL = "sequential"     # Single-threaded execution
    THREADED = "threaded"        # Multi-threaded execution
    PROCESS = "process"          # Multi-process execution
    ASYNC = "async"              # Asynchronous execution
    HYBRID = "hybrid"            # Combination of threading and async


@dataclass
class ExecutionConfig:
    """Configuration for parallel execution."""
    mode: ExecutionMode = ExecutionMode.THREADED
    max_workers: Optional[int] = None
    chunk_size: int = 10
    timeout: Optional[float] = 30.0
    preserve_order: bool = True
    error_handling: str = "continue"  # "continue", "stop", "collect"


@dataclass
class ExecutionResult:
    """Result of parallel execution."""
    results: List[Any]
    errors: List[Exception]
    execution_time: float
    worker_count: int
    mode: ExecutionMode
    
    @property
    def success_count(self) -> int:
        return len(self.results) - len(self.errors)
    
    @property
    def error_count(self) -> int:
        return len(self.errors)
    
    @property
    def success_rate(self) -> float:
        total = len(self.results)
        return self.success_count / total if total > 0 else 0.0


class ParallelExecutor:
    """
    High-performance parallel executor for tactical RPG operations.
    
    Features:
    - Multiple execution modes (threaded, process, async)
    - Automatic worker scaling
    - Batch processing optimization
    - Error handling and recovery
    - Performance monitoring
    - Memory-efficient processing
    """
    
    def __init__(self, default_config: Optional[ExecutionConfig] = None):
        self.default_config = default_config or ExecutionConfig()
        
        # Execution pools
        self._thread_pool: Optional[ThreadPoolExecutor] = None
        self._process_pool: Optional[ProcessPoolExecutor] = None
        self._async_loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Performance tracking
        self.execution_history: List[ExecutionResult] = []
        self.lock = threading.RLock()
        
        # Auto-scaling parameters
        self.min_workers = 2
        self.max_workers = min(32, (multiprocessing.cpu_count() or 1) * 4)
        self.optimal_workers = multiprocessing.cpu_count() or 1
        
        print(f"⚡ Parallel Executor initialized (optimal_workers={self.optimal_workers})")
    
    def _get_optimal_worker_count(self, task_count: int, mode: ExecutionMode) -> int:
        """Determine optimal worker count for given tasks."""
        if mode == ExecutionMode.SEQUENTIAL:
            return 1
        
        # Base on CPU count and task characteristics
        cpu_count = multiprocessing.cpu_count() or 1
        
        if mode == ExecutionMode.PROCESS:
            # Process pool - limited by CPU cores
            return min(task_count, cpu_count, self.max_workers)
        
        elif mode == ExecutionMode.THREADED:
            # Thread pool - can be higher than CPU count for I/O bound tasks
            return min(task_count, cpu_count * 2, self.max_workers)
        
        elif mode == ExecutionMode.ASYNC:
            # Async - single event loop with high concurrency
            return min(task_count, 100)  # Reasonable concurrent limit
        
        return min(task_count, self.optimal_workers)
    
    def _get_thread_pool(self, worker_count: int) -> ThreadPoolExecutor:
        """Get or create thread pool."""
        if (self._thread_pool is None or 
            self._thread_pool._max_workers != worker_count):
            if self._thread_pool:
                self._thread_pool.shutdown(wait=False)
            self._thread_pool = ThreadPoolExecutor(max_workers=worker_count)
        return self._thread_pool
    
    def _get_process_pool(self, worker_count: int) -> ProcessPoolExecutor:
        """Get or create process pool."""
        if (self._process_pool is None or 
            self._process_pool._max_workers != worker_count):
            if self._process_pool:
                self._process_pool.shutdown(wait=False)
            self._process_pool = ProcessPoolExecutor(max_workers=worker_count)
        return self._process_pool
    
    def execute_parallel(self, 
                        func: Callable,
                        items: List[Any],
                        config: Optional[ExecutionConfig] = None) -> ExecutionResult:
        """
        Execute function in parallel on list of items.
        
        Args:
            func: Function to execute
            items: List of items to process
            config: Execution configuration
            
        Returns:
            ExecutionResult with results and performance data
        """
        config = config or self.default_config
        start_time = time.time()
        
        if not items:
            return ExecutionResult([], [], 0.0, 0, config.mode)
        
        worker_count = self._get_optimal_worker_count(len(items), config.mode)
        
        try:
            if config.mode == ExecutionMode.SEQUENTIAL:
                results, errors = self._execute_sequential(func, items, config)
            elif config.mode == ExecutionMode.THREADED:
                results, errors = self._execute_threaded(func, items, config, worker_count)
            elif config.mode == ExecutionMode.PROCESS:
                results, errors = self._execute_process(func, items, config, worker_count)
            elif config.mode == ExecutionMode.ASYNC:
                results, errors = self._execute_async(func, items, config)
            elif config.mode == ExecutionMode.HYBRID:
                results, errors = self._execute_hybrid(func, items, config, worker_count)
            else:
                raise ValueError(f"Unknown execution mode: {config.mode}")
            
        except Exception as e:
            # Fallback to sequential on error
            print(f"⚠️ Parallel execution failed, falling back to sequential: {e}")
            results, errors = self._execute_sequential(func, items, config)
            worker_count = 1
        
        execution_time = time.time() - start_time
        
        result = ExecutionResult(
            results=results,
            errors=errors,
            execution_time=execution_time,
            worker_count=worker_count,
            mode=config.mode
        )
        
        # Track performance
        with self.lock:
            self.execution_history.append(result)
            if len(self.execution_history) > 100:  # Keep last 100 results
                self.execution_history.pop(0)
        
        return result
    
    def _execute_sequential(self, func: Callable, items: List[Any], 
                           config: ExecutionConfig) -> Tuple[List[Any], List[Exception]]:
        """Execute sequentially."""
        results = []
        errors = []
        
        for item in items:
            try:
                result = func(item)
                results.append(result)
            except Exception as e:
                errors.append(e)
                if config.error_handling == "stop":
                    break
                elif config.error_handling == "continue":
                    results.append(None)  # Placeholder for failed item
        
        return results, errors
    
    def _execute_threaded(self, func: Callable, items: List[Any],
                         config: ExecutionConfig, worker_count: int) -> Tuple[List[Any], List[Exception]]:
        """Execute using thread pool."""
        pool = self._get_thread_pool(worker_count)
        results = [None] * len(items)
        errors = []
        
        # Submit all tasks
        future_to_index = {}
        for i, item in enumerate(items):
            future = pool.submit(func, item)
            future_to_index[future] = i
        
        # Collect results
        for future in as_completed(future_to_index.keys(), timeout=config.timeout):
            index = future_to_index[future]
            try:
                result = future.result()
                results[index] = result
            except Exception as e:
                errors.append(e)
                if config.error_handling == "stop":
                    # Cancel remaining futures
                    for f in future_to_index.keys():
                        f.cancel()
                    break
        
        return results, errors
    
    def _execute_process(self, func: Callable, items: List[Any],
                        config: ExecutionConfig, worker_count: int) -> Tuple[List[Any], List[Exception]]:
        """Execute using process pool."""
        pool = self._get_process_pool(worker_count)
        results = [None] * len(items)
        errors = []
        
        # Submit all tasks
        future_to_index = {}
        for i, item in enumerate(items):
            future = pool.submit(func, item)
            future_to_index[future] = i
        
        # Collect results
        for future in as_completed(future_to_index.keys(), timeout=config.timeout):
            index = future_to_index[future]
            try:
                result = future.result()
                results[index] = result
            except Exception as e:
                errors.append(e)
                if config.error_handling == "stop":
                    break
        
        return results, errors
    
    def _execute_async(self, func: Callable, items: List[Any],
                      config: ExecutionConfig) -> Tuple[List[Any], List[Exception]]:
        """Execute using async/await."""
        # Create new event loop if needed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Convert sync function to async
        async def async_func(item):
            # Run in thread pool to avoid blocking
            return await loop.run_in_executor(None, func, item)
        
        async def run_all():
            tasks = [async_func(item) for item in items]
            results = []
            errors = []
            
            for coro in asyncio.as_completed(tasks, timeout=config.timeout):
                try:
                    result = await coro
                    results.append(result)
                except Exception as e:
                    errors.append(e)
                    if config.error_handling == "stop":
                        break
            
            return results, errors
        
        return loop.run_until_complete(run_all())
    
    def _execute_hybrid(self, func: Callable, items: List[Any],
                       config: ExecutionConfig, worker_count: int) -> Tuple[List[Any], List[Exception]]:
        """Execute using hybrid approach (threading + async)."""
        # For now, use threaded execution
        # In future, could implement more sophisticated hybrid strategies
        return self._execute_threaded(func, items, config, worker_count)
    
    def batch_execute(self, func: Callable, items: List[Any],
                     batch_size: Optional[int] = None,
                     config: Optional[ExecutionConfig] = None) -> ExecutionResult:
        """
        Execute function on items in batches for memory efficiency.
        
        Args:
            func: Function to execute
            items: Items to process
            batch_size: Size of each batch (auto-calculated if None)
            config: Execution configuration
            
        Returns:
            Combined execution result
        """
        config = config or self.default_config
        
        if batch_size is None:
            # Auto-calculate batch size based on available memory and item count
            batch_size = max(1, min(len(items) // 4, 100))
        
        all_results = []
        all_errors = []
        total_time = 0.0
        total_workers = 0
        
        # Process in batches
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            result = self.execute_parallel(func, batch, config)
            
            all_results.extend(result.results)
            all_errors.extend(result.errors)
            total_time += result.execution_time
            total_workers = max(total_workers, result.worker_count)
        
        return ExecutionResult(
            results=all_results,
            errors=all_errors,
            execution_time=total_time,
            worker_count=total_workers,
            mode=config.mode
        )
    
    def parallel_map(self, func: Callable, items: List[Any],
                    config: Optional[ExecutionConfig] = None) -> List[Any]:
        """
        Parallel map function (similar to built-in map).
        
        Args:
            func: Function to apply
            items: Items to process
            config: Execution configuration
            
        Returns:
            List of results (same order as input)
        """
        result = self.execute_parallel(func, items, config)
        return result.results
    
    def parallel_filter(self, predicate: Callable, items: List[Any],
                       config: Optional[ExecutionConfig] = None) -> List[Any]:
        """
        Parallel filter function.
        
        Args:
            predicate: Filter predicate
            items: Items to filter
            config: Execution configuration
            
        Returns:
            Filtered list of items
        """
        # Create function that returns (item, keep) tuples
        def filter_func(item):
            return (item, predicate(item))
        
        result = self.execute_parallel(filter_func, items, config)
        
        # Extract items where predicate was True
        return [item for item, keep in result.results if keep]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        with self.lock:
            if not self.execution_history:
                return {}
            
            # Calculate aggregate statistics
            total_executions = len(self.execution_history)
            avg_execution_time = sum(r.execution_time for r in self.execution_history) / total_executions
            avg_success_rate = sum(r.success_rate for r in self.execution_history) / total_executions
            
            # Mode usage
            mode_counts = {}
            for result in self.execution_history:
                mode = result.mode.value
                mode_counts[mode] = mode_counts.get(mode, 0) + 1
            
            return {
                'total_executions': total_executions,
                'avg_execution_time': avg_execution_time,
                'avg_success_rate': avg_success_rate,
                'mode_usage': mode_counts,
                'optimal_workers': self.optimal_workers,
                'recent_executions': len([r for r in self.execution_history 
                                        if time.time() - r.execution_time < 300])  # Last 5 minutes
            }
    
    @contextmanager
    def execution_context(self, config: ExecutionConfig):
        """Context manager for temporary execution configuration."""
        old_config = self.default_config
        self.default_config = config
        try:
            yield
        finally:
            self.default_config = old_config
    
    def shutdown(self):
        """Shutdown all execution pools."""
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True)
            self._thread_pool = None
        
        if self._process_pool:
            self._process_pool.shutdown(wait=True)
            self._process_pool = None
        
        print("⚡ Parallel Executor shut down")


# Global parallel executor instance
parallel_executor = ParallelExecutor()


# Convenience functions
def parallel_execute(func: Callable, items: List[Any], 
                    mode: ExecutionMode = ExecutionMode.THREADED,
                    max_workers: Optional[int] = None) -> ExecutionResult:
    """Execute function in parallel on items."""
    config = ExecutionConfig(mode=mode, max_workers=max_workers)
    return parallel_executor.execute_parallel(func, items, config)


def parallel_map(func: Callable, items: List[Any],
                mode: ExecutionMode = ExecutionMode.THREADED) -> List[Any]:
    """Parallel map function."""
    config = ExecutionConfig(mode=mode)
    return parallel_executor.parallel_map(func, items, config)


def async_execute(func: Callable, items: List[Any]) -> ExecutionResult:
    """Execute function asynchronously."""
    config = ExecutionConfig(mode=ExecutionMode.ASYNC)
    return parallel_executor.execute_parallel(func, items, config)


# Decorators for automatic parallelization
def parallelize(mode: ExecutionMode = ExecutionMode.THREADED,
               chunk_size: int = 10):
    """
    Decorator to automatically parallelize functions that work on lists.
    
    The decorated function should accept a list as its first argument
    and return a list of the same length.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(items: List[Any], *args, **kwargs):
            if len(items) < chunk_size:
                # Too few items, execute sequentially
                return func(items, *args, **kwargs)
            
            # Create partial function with additional arguments
            partial_func = functools.partial(func, *args, **kwargs)
            
            config = ExecutionConfig(mode=mode, chunk_size=chunk_size)
            result = parallel_executor.execute_parallel(partial_func, items, config)
            
            return result.results
        
        return wrapper
    return decorator


@parallelize(mode=ExecutionMode.THREADED)
def parallel_stat_calculation(units: List[Any]) -> List[Dict[str, Any]]:
    """Example: Parallel stat calculation for multiple units."""
    def calculate_unit_stats(unit):
        # Placeholder for actual stat calculation
        return {
            'unit_id': getattr(unit, 'id', 'unknown'),
            'hp': getattr(unit, 'hp', 0),
            'mp': getattr(unit, 'mp', 0),
            'calculated_at': time.time()
        }
    
    return [calculate_unit_stats(unit) for unit in units]