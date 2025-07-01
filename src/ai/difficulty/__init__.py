"""
AI Difficulty Scaling Package

Dynamic difficulty system that adapts AI behavior based on player performance.
"""

from .difficulty_manager import DifficultyManager, AIDifficulty
from .adaptive_scaling import AdaptiveScaling, PerformanceMetrics

__all__ = [
    'DifficultyManager',
    'AIDifficulty', 
    'AdaptiveScaling',
    'PerformanceMetrics'
]