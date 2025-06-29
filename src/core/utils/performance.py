"""
Performance Monitoring System

Tracks performance metrics with minimal overhead.
Provides frame timing and system performance analysis.
"""

import time
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from collections import deque

class PerformanceMonitor:
    """
    Performance monitoring and profiling system.
    
    Tracks frame times, system performance, and provides
    detailed analysis with minimal runtime overhead.
    """
    
    def __init__(self, history_size: int = 120):  # 2 seconds at 60 FPS
        self.history_size = history_size
        self.frame_times = deque(maxlen=history_size)
        self.measurements = {}
        self.active = True
        
        # Performance targets from Advanced-Implementation-Guide.md
        self.performance_targets = {
            'stat_calculation': 0.001,  # 1ms
            'pathfinding': 0.002,       # 2ms
            'visual_update': 0.005,     # 5ms
            'ai_decision': 0.100,       # 100ms
            'frame_time': 0.016         # 16ms (60 FPS)
        }
        
        self.warnings = []
        self.start_time = time.perf_counter()
    
    def start(self):
        """Start performance monitoring"""
        self.active = True
        self.start_time = time.perf_counter()
    
    def stop(self):
        """Stop performance monitoring"""
        self.active = False
    
    @contextmanager
    def measure(self, operation_name: str):
        """
        Context manager for measuring operation performance.
        
        Args:
            operation_name: Name of operation being measured
            
        Usage:
            with monitor.measure("stat_calculation"):
                calculate_stats()
        """
        if not self.active:
            yield
            return
        
        start_time = time.perf_counter()
        try:
            yield
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time
            self._record_measurement(operation_name, duration)
    
    def _record_measurement(self, operation_name: str, duration: float):
        """Record performance measurement"""
        if operation_name not in self.measurements:
            self.measurements[operation_name] = deque(maxlen=self.history_size)
        
        self.measurements[operation_name].append(duration)
        
        # Check against performance targets
        target = self.performance_targets.get(operation_name)
        if target and duration > target:
            warning = {
                'operation': operation_name,
                'duration': duration,
                'target': target,
                'timestamp': time.time()
            }
            self.warnings.append(warning)
            
            # Keep only recent warnings
            if len(self.warnings) > 100:
                self.warnings = self.warnings[-50:]
    
    def update(self, delta_time: float):
        """
        Update performance monitor each frame.
        
        Args:
            delta_time: Time since last frame
        """
        if not self.active:
            return
        
        # Record frame time
        self.frame_times.append(delta_time)
        
        # Check frame time target
        target = self.performance_targets.get('frame_time', 0.016)
        if delta_time > target:
            self._record_measurement('frame_time', delta_time)
    
    def get_average_time(self, operation_name: str) -> float:
        """
        Get average time for operation.
        
        Args:
            operation_name: Name of operation
            
        Returns:
            Average time in seconds, or 0 if no measurements
        """
        measurements = self.measurements.get(operation_name, [])
        return sum(measurements) / len(measurements) if measurements else 0.0
    
    def get_max_time(self, operation_name: str) -> float:
        """
        Get maximum time for operation.
        
        Args:
            operation_name: Name of operation
            
        Returns:
            Maximum time in seconds, or 0 if no measurements
        """
        measurements = self.measurements.get(operation_name, [])
        return max(measurements) if measurements else 0.0
    
    def get_fps(self) -> float:
        """Get current average FPS"""
        if not self.frame_times:
            return 0.0
        
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0
    
    def get_frame_time_ms(self) -> float:
        """Get current average frame time in milliseconds"""
        if not self.frame_times:
            return 0.0
        
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return avg_frame_time * 1000.0
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.
        
        Returns:
            Dictionary containing performance statistics
        """
        report = {
            'uptime': time.perf_counter() - self.start_time,
            'fps': self.get_fps(),
            'average_frame_time_ms': self.get_frame_time_ms(),
            'measurements': {},
            'warnings': len(self.warnings),
            'recent_warnings': self.warnings[-10:] if self.warnings else []
        }
        
        # Add measurement statistics
        for operation_name, measurements in self.measurements.items():
            if measurements:
                report['measurements'][operation_name] = {
                    'count': len(measurements),
                    'average_ms': self.get_average_time(operation_name) * 1000,
                    'max_ms': self.get_max_time(operation_name) * 1000,
                    'target_ms': self.performance_targets.get(operation_name, 0) * 1000
                }
        
        return report
    
    def check_performance_targets(self) -> List[Dict[str, Any]]:
        """
        Check if all operations meet performance targets.
        
        Returns:
            List of operations exceeding targets
        """
        violations = []
        
        for operation_name, target in self.performance_targets.items():
            avg_time = self.get_average_time(operation_name)
            if avg_time > target:
                violations.append({
                    'operation': operation_name,
                    'average_time': avg_time,
                    'target': target,
                    'ratio': avg_time / target
                })
        
        return violations
    
    def reset_measurements(self):
        """Reset all performance measurements"""
        self.measurements.clear()
        self.frame_times.clear()
        self.warnings.clear()
        self.start_time = time.perf_counter()