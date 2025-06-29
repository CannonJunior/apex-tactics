"""
Performance Profiler

Performance monitoring and profiling utilities for the tactical RPG engine.
"""

import time
import statistics
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from contextlib import contextmanager
from collections import defaultdict


@dataclass
class PerformanceMetric:
    """Individual performance measurement"""
    name: str
    duration: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceStats:
    """Aggregated performance statistics"""
    name: str
    total_calls: int
    total_time: float
    min_time: float
    max_time: float
    average_time: float
    median_time: float
    last_measurement: float
    
    @property
    def calls_per_second(self) -> float:
        """Calculate calls per second over total runtime"""
        if self.total_time > 0:
            return self.total_calls / self.total_time
        return 0.0


class PerformanceProfiler:
    """
    Performance profiling system for monitoring engine performance.
    
    Tracks execution times, memory usage, and system performance metrics
    to ensure performance targets are met.
    """
    
    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples
        self.measurements: Dict[str, List[PerformanceMetric]] = defaultdict(list)
        self.active_timers: Dict[str, float] = {}
        
        # Performance targets (from Advanced-Implementation-Guide.md)
        self.performance_targets = {
            'stat_calculations': 0.001,      # <1ms for complex character sheets
            'pathfinding': 0.002,           # <2ms per query on 10x10 grids
            'visual_updates': 0.005,        # <5ms for full battlefield refresh
            'ai_decisions': 0.100,          # <100ms per unit turn
            'frame_time': 0.016,            # ~60 FPS (16ms per frame)
        }
        
        # Warnings and alerts
        self.warning_threshold_multiplier = 1.5  # Warn at 150% of target
        self.critical_threshold_multiplier = 2.0  # Critical at 200% of target
        
        # Performance history for trend analysis
        self.performance_history: List[Dict[str, float]] = []
        self.history_interval = 1.0  # seconds
        self.last_history_time = time.time()
    
    @contextmanager
    def measure(self, operation_name: str, **metadata):
        """Context manager for measuring operation performance"""
        start_time = time.perf_counter()
        
        try:
            yield
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            self.record_measurement(operation_name, duration, **metadata)
    
    def start_timer(self, operation_name: str):
        """Start a named timer"""
        self.active_timers[operation_name] = time.perf_counter()
    
    def stop_timer(self, operation_name: str, **metadata) -> float:
        """Stop a named timer and record the measurement"""
        if operation_name not in self.active_timers:
            raise ValueError(f"Timer '{operation_name}' was not started")
        
        start_time = self.active_timers.pop(operation_name)
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        self.record_measurement(operation_name, duration, **metadata)
        return duration
    
    def record_measurement(self, operation_name: str, duration: float, **metadata):
        """Record a performance measurement"""
        metric = PerformanceMetric(
            name=operation_name,
            duration=duration,
            timestamp=time.time(),
            metadata=metadata
        )
        
        self.measurements[operation_name].append(metric)
        
        # Limit sample size to prevent memory growth
        if len(self.measurements[operation_name]) > self.max_samples:
            self.measurements[operation_name] = self.measurements[operation_name][-self.max_samples:]
        
        # Check for performance issues
        self._check_performance_threshold(operation_name, duration)
        
        # Update performance history
        self._update_performance_history()
    
    def _check_performance_threshold(self, operation_name: str, duration: float):
        """Check if measurement exceeds performance thresholds"""
        target = self.performance_targets.get(operation_name)
        if target is None:
            return
        
        warning_threshold = target * self.warning_threshold_multiplier
        critical_threshold = target * self.critical_threshold_multiplier
        
        if duration > critical_threshold:
            print(f"CRITICAL: {operation_name} took {duration*1000:.2f}ms "
                  f"(target: {target*1000:.2f}ms, critical: {critical_threshold*1000:.2f}ms)")
        elif duration > warning_threshold:
            print(f"WARNING: {operation_name} took {duration*1000:.2f}ms "
                  f"(target: {target*1000:.2f}ms, warning: {warning_threshold*1000:.2f}ms)")
    
    def _update_performance_history(self):
        """Update performance history for trend analysis"""
        current_time = time.time()
        
        if current_time - self.last_history_time >= self.history_interval:
            # Calculate average performance for each operation in the last interval
            history_entry = {}
            
            for operation_name, metrics in self.measurements.items():
                recent_metrics = [m for m in metrics 
                                if current_time - m.timestamp <= self.history_interval]
                
                if recent_metrics:
                    avg_duration = statistics.mean(m.duration for m in recent_metrics)
                    history_entry[operation_name] = avg_duration
            
            if history_entry:
                self.performance_history.append(history_entry)
                
                # Limit history size
                if len(self.performance_history) > 300:  # 5 minutes at 1-second intervals
                    self.performance_history = self.performance_history[-300:]
            
            self.last_history_time = current_time
    
    def get_stats(self, operation_name: str) -> Optional[PerformanceStats]:
        """Get aggregated statistics for an operation"""
        if operation_name not in self.measurements:
            return None
        
        metrics = self.measurements[operation_name]
        if not metrics:
            return None
        
        durations = [m.duration for m in metrics]
        
        return PerformanceStats(
            name=operation_name,
            total_calls=len(durations),
            total_time=sum(durations),
            min_time=min(durations),
            max_time=max(durations),
            average_time=statistics.mean(durations),
            median_time=statistics.median(durations),
            last_measurement=durations[-1]
        )
    
    def get_all_stats(self) -> Dict[str, PerformanceStats]:
        """Get statistics for all measured operations"""
        return {name: self.get_stats(name) 
                for name in self.measurements.keys() 
                if self.get_stats(name) is not None}
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        all_stats = self.get_all_stats()
        
        # Check target compliance
        target_compliance = {}
        for operation_name, target in self.performance_targets.items():
            stats = all_stats.get(operation_name)
            if stats:
                compliance_ratio = stats.average_time / target
                target_compliance[operation_name] = {
                    'target_ms': target * 1000,
                    'average_ms': stats.average_time * 1000,
                    'compliance_ratio': compliance_ratio,
                    'meets_target': compliance_ratio <= 1.0,
                    'status': ('PASS' if compliance_ratio <= 1.0 
                             else 'WARN' if compliance_ratio <= 1.5 
                             else 'FAIL')
                }
        
        # Performance trends
        trends = self._analyze_performance_trends()
        
        return {
            'timestamp': time.time(),
            'measurement_count': sum(len(metrics) for metrics in self.measurements.values()),
            'operations_tracked': len(self.measurements),
            'target_compliance': target_compliance,
            'performance_stats': {name: {
                'total_calls': stats.total_calls,
                'average_ms': stats.average_time * 1000,
                'min_ms': stats.min_time * 1000,
                'max_ms': stats.max_time * 1000,
                'median_ms': stats.median_time * 1000,
                'calls_per_second': stats.calls_per_second
            } for name, stats in all_stats.items()},
            'performance_trends': trends,
            'memory_usage': self._get_memory_usage()
        }
    
    def _analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends over time"""
        if len(self.performance_history) < 2:
            return {}
        
        trends = {}
        
        for operation_name in self.performance_targets.keys():
            # Get recent measurements
            recent_values = []
            for entry in self.performance_history[-30:]:  # Last 30 seconds
                if operation_name in entry:
                    recent_values.append(entry[operation_name])
            
            if len(recent_values) >= 5:
                # Calculate trend (simple linear regression slope)
                x_values = list(range(len(recent_values)))
                y_values = recent_values
                
                n = len(recent_values)
                sum_x = sum(x_values)
                sum_y = sum(y_values)
                sum_xy = sum(x * y for x, y in zip(x_values, y_values))
                sum_x_squared = sum(x * x for x in x_values)
                
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x_squared - sum_x * sum_x)
                
                trends[operation_name] = {
                    'slope_ms_per_second': slope * 1000,
                    'trend': ('improving' if slope < -0.001 
                            else 'degrading' if slope > 0.001 
                            else 'stable'),
                    'recent_average_ms': statistics.mean(recent_values) * 1000,
                    'sample_count': len(recent_values)
                }
        
        return trends
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage information"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss_mb': memory_info.rss / (1024 * 1024),
                'vms_mb': memory_info.vms / (1024 * 1024),
                'percent': process.memory_percent(),
                'available': True
            }
        except ImportError:
            return {'available': False, 'error': 'psutil not installed'}
    
    def print_performance_summary(self):
        """Print a formatted performance summary"""
        print("\n=== Performance Summary ===")
        
        all_stats = self.get_all_stats()
        
        # Print target compliance
        print("\nTarget Compliance:")
        for operation_name, target in self.performance_targets.items():
            stats = all_stats.get(operation_name)
            if stats:
                ratio = stats.average_time / target
                status = "✓" if ratio <= 1.0 else "⚠" if ratio <= 1.5 else "✗"
                print(f"  {status} {operation_name}: {stats.average_time*1000:.2f}ms "
                      f"(target: {target*1000:.2f}ms, ratio: {ratio:.2f})")
            else:
                print(f"  - {operation_name}: No measurements")
        
        # Print detailed stats
        print("\nDetailed Statistics:")
        for name, stats in all_stats.items():
            print(f"  {name}:")
            print(f"    Calls: {stats.total_calls}")
            print(f"    Average: {stats.average_time*1000:.2f}ms")
            print(f"    Min/Max: {stats.min_time*1000:.2f}ms / {stats.max_time*1000:.2f}ms")
            print(f"    Median: {stats.median_time*1000:.2f}ms")
            if stats.calls_per_second > 0:
                print(f"    Rate: {stats.calls_per_second:.1f} calls/sec")
    
    def reset(self):
        """Reset all measurements"""
        self.measurements.clear()
        self.active_timers.clear()
        self.performance_history.clear()
        self.last_history_time = time.time()
    
    def export_measurements(self, filename: str):
        """Export measurements to CSV file"""
        import csv
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['operation', 'duration_ms', 'timestamp', 'metadata'])
            
            for operation_name, metrics in self.measurements.items():
                for metric in metrics:
                    writer.writerow([
                        operation_name,
                        metric.duration * 1000,
                        metric.timestamp,
                        str(metric.metadata)
                    ])
        
        print(f"Performance measurements exported to {filename}")


# Global profiler instance
profiler = PerformanceProfiler()


# Decorator for easy profiling
def profile_performance(operation_name: str):
    """Decorator to automatically profile function performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with profiler.measure(operation_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator