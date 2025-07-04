"""
Performance Profiler System

Comprehensive profiling and performance analysis for identifying
bottlenecks and optimization opportunities in the tactical RPG engine.
"""

import time
import threading
import statistics
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from contextlib import contextmanager
from collections import defaultdict, deque
import functools
import traceback


@dataclass
class ProfileResult:
    """Result of a profiling measurement."""
    name: str
    duration: float
    start_time: float
    end_time: float
    thread_id: int
    call_count: int = 1
    memory_delta: Optional[int] = None
    cpu_percent: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class AggregatedProfile:
    """Aggregated profiling statistics for multiple calls."""
    name: str
    total_calls: int
    total_duration: float
    avg_duration: float
    min_duration: float
    max_duration: float
    median_duration: float
    std_dev: float
    percentile_95: float
    percentile_99: float
    call_frequency: float  # calls per second


class PerformanceProfiler:
    """
    Advanced performance profiler for tactical RPG systems.
    
    Features:
    - Function-level profiling with decorators
    - Context manager profiling  
    - Thread-safe operation
    - Statistical analysis
    - Memory tracking
    - Call frequency analysis
    - Bottleneck identification
    """
    
    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self.profiles: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.active_contexts: Dict[int, List[str]] = defaultdict(list)
        self.lock = threading.RLock()
        self.enabled = True
        
        # Performance tracking
        self.start_time = time.time()
        self.total_profiles = 0
        
        print("⚡ Performance Profiler initialized")
    
    def enable(self):
        """Enable profiling."""
        self.enabled = True
        print("⚡ Profiler enabled")
    
    def disable(self):
        """Disable profiling."""
        self.enabled = False
        print("⚡ Profiler disabled")
    
    def profile_function(self, name: Optional[str] = None):
        """
        Decorator for function profiling.
        
        Args:
            name: Optional custom name for the profile
        """
        def decorator(func: Callable) -> Callable:
            profile_name = name or f"{func.__module__}.{func.__name__}"
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)
                
                with self.profile_context(profile_name):
                    return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    @contextmanager
    def profile_context(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager for profiling code blocks.
        
        Args:
            name: Name of the operation being profiled
            metadata: Additional metadata to store with the profile
        """
        if not self.enabled:
            yield
            return
        
        thread_id = threading.get_ident()
        start_time = time.perf_counter()
        start_memory = self._get_memory_usage()
        
        try:
            with self.lock:
                self.active_contexts[thread_id].append(name)
            
            yield
            
        finally:
            end_time = time.perf_counter()
            end_memory = self._get_memory_usage()
            duration = end_time - start_time
            
            memory_delta = None
            if start_memory is not None and end_memory is not None:
                memory_delta = end_memory - start_memory
            
            result = ProfileResult(
                name=name,
                duration=duration,
                start_time=start_time,
                end_time=end_time,
                thread_id=thread_id,
                memory_delta=memory_delta,
                metadata=metadata or {}
            )
            
            with self.lock:
                self.profiles[name].append(result)
                self.active_contexts[thread_id].pop()
                self.total_profiles += 1
    
    def _get_memory_usage(self) -> Optional[int]:
        """Get current memory usage in bytes."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss
        except ImportError:
            return None
    
    def get_profile_summary(self, name: str) -> Optional[AggregatedProfile]:
        """Get aggregated profile statistics for a named operation."""
        with self.lock:
            if name not in self.profiles or not self.profiles[name]:
                return None
            
            results = list(self.profiles[name])
            durations = [r.duration for r in results]
            
            if not durations:
                return None
            
            # Calculate time span for frequency
            time_span = max(r.end_time for r in results) - min(r.start_time for r in results)
            frequency = len(results) / max(time_span, 0.001)  # Avoid division by zero
            
            # Calculate percentiles
            sorted_durations = sorted(durations)
            n = len(sorted_durations)
            p95_idx = int(0.95 * n)
            p99_idx = int(0.99 * n)
            
            return AggregatedProfile(
                name=name,
                total_calls=len(results),
                total_duration=sum(durations),
                avg_duration=statistics.mean(durations),
                min_duration=min(durations),
                max_duration=max(durations),
                median_duration=statistics.median(durations),
                std_dev=statistics.stdev(durations) if len(durations) > 1 else 0.0,
                percentile_95=sorted_durations[p95_idx] if p95_idx < n else sorted_durations[-1],
                percentile_99=sorted_durations[p99_idx] if p99_idx < n else sorted_durations[-1],
                call_frequency=frequency
            )
    
    def get_all_profiles(self) -> Dict[str, AggregatedProfile]:
        """Get aggregated profiles for all operations."""
        profiles = {}
        with self.lock:
            for name in self.profiles.keys():
                summary = self.get_profile_summary(name)
                if summary:
                    profiles[name] = summary
        return profiles
    
    def get_bottlenecks(self, top_n: int = 10) -> List[AggregatedProfile]:
        """
        Identify performance bottlenecks.
        
        Args:
            top_n: Number of top bottlenecks to return
            
        Returns:
            List of profiles sorted by total time spent
        """
        all_profiles = self.get_all_profiles()
        sorted_profiles = sorted(
            all_profiles.values(),
            key=lambda p: p.total_duration,
            reverse=True
        )
        return sorted_profiles[:top_n]
    
    def get_slow_operations(self, threshold_ms: float = 10.0) -> List[AggregatedProfile]:
        """
        Get operations that are consistently slow.
        
        Args:
            threshold_ms: Average duration threshold in milliseconds
            
        Returns:
            List of operations with avg duration above threshold
        """
        threshold_s = threshold_ms / 1000.0
        all_profiles = self.get_all_profiles()
        
        slow_ops = [
            profile for profile in all_profiles.values()
            if profile.avg_duration > threshold_s
        ]
        
        return sorted(slow_ops, key=lambda p: p.avg_duration, reverse=True)
    
    def get_frequent_operations(self, min_frequency: float = 10.0) -> List[AggregatedProfile]:
        """
        Get operations called very frequently.
        
        Args:
            min_frequency: Minimum calls per second threshold
            
        Returns:
            List of frequently called operations
        """
        all_profiles = self.get_all_profiles()
        
        frequent_ops = [
            profile for profile in all_profiles.values()
            if profile.call_frequency > min_frequency
        ]
        
        return sorted(frequent_ops, key=lambda p: p.call_frequency, reverse=True)
    
    def generate_report(self) -> str:
        """Generate comprehensive performance report."""
        report = []
        report.append("=" * 80)
        report.append("PERFORMANCE PROFILING REPORT")
        report.append("=" * 80)
        
        # Summary statistics
        uptime = time.time() - self.start_time
        report.append(f"Profiler Uptime: {uptime:.2f}s")
        report.append(f"Total Profiles: {self.total_profiles}")
        report.append(f"Active Operations: {len(self.profiles)}")
        report.append("")
        
        # Top bottlenecks
        bottlenecks = self.get_bottlenecks(10)
        if bottlenecks:
            report.append("🔥 TOP BOTTLENECKS (by total time)")
            report.append("-" * 50)
            for i, profile in enumerate(bottlenecks, 1):
                report.append(
                    f"{i:2d}. {profile.name:<30} "
                    f"{profile.total_duration*1000:8.2f}ms total "
                    f"({profile.total_calls:4d} calls, "
                    f"{profile.avg_duration*1000:6.2f}ms avg)"
                )
            report.append("")
        
        # Slow operations  
        slow_ops = self.get_slow_operations(5.0)  # 5ms threshold
        if slow_ops:
            report.append("🐌 SLOW OPERATIONS (avg > 5ms)")
            report.append("-" * 50)
            for i, profile in enumerate(slow_ops, 1):
                report.append(
                    f"{i:2d}. {profile.name:<30} "
                    f"{profile.avg_duration*1000:6.2f}ms avg "
                    f"(min: {profile.min_duration*1000:5.2f}ms, "
                    f"max: {profile.max_duration*1000:5.2f}ms)"
                )
            report.append("")
        
        # Frequent operations
        frequent_ops = self.get_frequent_operations(5.0)  # 5 calls/sec threshold
        if frequent_ops:
            report.append("🔄 FREQUENT OPERATIONS (> 5 calls/sec)")
            report.append("-" * 50)
            for i, profile in enumerate(frequent_ops, 1):
                report.append(
                    f"{i:2d}. {profile.name:<30} "
                    f"{profile.call_frequency:6.1f} calls/sec "
                    f"({profile.total_calls:4d} total calls)"
                )
            report.append("")
        
        # Performance recommendations
        report.append("💡 OPTIMIZATION RECOMMENDATIONS")
        report.append("-" * 50)
        
        recommendations = []
        
        # Check for expensive frequent operations
        for profile in frequent_ops:
            if profile.avg_duration > 0.001:  # 1ms
                recommendations.append(
                    f"• Optimize '{profile.name}' - called {profile.call_frequency:.1f}x/sec "
                    f"with {profile.avg_duration*1000:.2f}ms avg duration"
                )
        
        # Check for high variability operations
        for profile in self.get_all_profiles().values():
            if profile.std_dev > profile.avg_duration * 0.5:  # High variability
                recommendations.append(
                    f"• Investigate '{profile.name}' - high variability "
                    f"(stddev: {profile.std_dev*1000:.2f}ms, avg: {profile.avg_duration*1000:.2f}ms)"
                )
        
        if not recommendations:
            recommendations.append("• No obvious optimization opportunities detected")
        
        report.extend(recommendations)
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def clear(self):
        """Clear all profiling data."""
        with self.lock:
            self.profiles.clear()
            self.active_contexts.clear()
            self.total_profiles = 0
        print("⚡ Profiler data cleared")
    
    def save_report(self, filename: str):
        """Save performance report to file."""
        report = self.generate_report()
        with open(filename, 'w') as f:
            f.write(report)
        print(f"⚡ Performance report saved to {filename}")


# Global profiler instance
profiler = PerformanceProfiler()


@contextmanager
def ProfilerContext(name: str, metadata: Optional[Dict[str, Any]] = None):
    """Convenience context manager for profiling."""
    with profiler.profile_context(name, metadata):
        yield


def profile(name: Optional[str] = None):
    """Convenience decorator for function profiling."""
    return profiler.profile_function(name)


# Performance analysis utilities
def analyze_action_system_performance():
    """Analyze performance of the action system specifically."""
    print("🔍 Analyzing Action System Performance...")
    
    action_profiles = {}
    all_profiles = profiler.get_all_profiles()
    
    # Filter action-related operations
    action_keywords = ['action', 'execute', 'queue', 'effect', 'combat', 'stat']
    
    for name, profile in all_profiles.items():
        if any(keyword in name.lower() for keyword in action_keywords):
            action_profiles[name] = profile
    
    if not action_profiles:
        print("  No action system profiles found")
        return
    
    # Analyze action bottlenecks
    sorted_actions = sorted(
        action_profiles.values(),
        key=lambda p: p.total_duration,
        reverse=True
    )
    
    print(f"  Found {len(action_profiles)} action system operations")
    print(f"  Top action bottlenecks:")
    
    for i, profile in enumerate(sorted_actions[:5], 1):
        efficiency = profile.total_calls / profile.total_duration if profile.total_duration > 0 else 0
        print(f"    {i}. {profile.name}")
        print(f"       Total: {profile.total_duration*1000:.2f}ms, "
              f"Avg: {profile.avg_duration*1000:.2f}ms, "
              f"Calls: {profile.total_calls}")
        print(f"       Efficiency: {efficiency:.1f} calls/sec")


def analyze_ai_performance():
    """Analyze AI system performance."""
    print("🤖 Analyzing AI System Performance...")
    
    ai_profiles = {}
    all_profiles = profiler.get_all_profiles()
    
    # Filter AI-related operations
    ai_keywords = ['ai', 'decision', 'mcp', 'agent', 'orchestrat', 'tactical']
    
    for name, profile in all_profiles.items():
        if any(keyword in name.lower() for keyword in ai_keywords):
            ai_profiles[name] = profile
    
    if not ai_profiles:
        print("  No AI system profiles found")
        return
    
    print(f"  Found {len(ai_profiles)} AI system operations")
    
    # Check decision latency
    decision_profiles = [p for p in ai_profiles.values() if 'decision' in p.name.lower()]
    if decision_profiles:
        avg_decision_time = sum(p.avg_duration for p in decision_profiles) / len(decision_profiles)
        print(f"  Average AI decision time: {avg_decision_time*1000:.2f}ms")
        
        if avg_decision_time > 0.1:  # 100ms threshold
            print("  ⚠️ AI decisions may be too slow for real-time gameplay")
        else:
            print("  ✅ AI decision latency within acceptable range")


def analyze_ui_performance():
    """Analyze UI system performance."""
    print("🖼️ Analyzing UI System Performance...")
    
    ui_profiles = {}
    all_profiles = profiler.get_all_profiles()
    
    # Filter UI-related operations
    ui_keywords = ['ui', 'update', 'render', 'display', 'interface', 'panel']
    
    for name, profile in all_profiles.items():
        if any(keyword in name.lower() for keyword in ui_keywords):
            ui_profiles[name] = profile
    
    if not ui_profiles:
        print("  No UI system profiles found")
        return
    
    print(f"  Found {len(ui_profiles)} UI system operations")
    
    # Check update frequency
    update_profiles = [p for p in ui_profiles.values() if 'update' in p.name.lower()]
    if update_profiles:
        total_updates = sum(p.total_calls for p in update_profiles)
        avg_frequency = sum(p.call_frequency for p in update_profiles) / len(update_profiles)
        print(f"  UI update frequency: {avg_frequency:.1f} updates/sec")
        print(f"  Total UI updates: {total_updates}")
        
        if avg_frequency > 60:  # More than 60 FPS
            print("  ⚠️ UI updating very frequently - consider throttling")
        elif avg_frequency < 10:  # Less than 10 FPS
            print("  ⚠️ UI updating infrequently - may feel unresponsive")
        else:
            print("  ✅ UI update frequency appropriate")