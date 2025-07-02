"""
Mathematical utilities for game calculations

Provides vector math, grid positions, and other mathematical
operations commonly used in tactical RPG games.
"""

import math
from typing import Tuple, Union
from dataclasses import dataclass


@dataclass
class Vector2:
    """2D vector for positions and directions"""
    x: float
    y: float
    
    def __add__(self, other: 'Vector2') -> 'Vector2':
        return Vector2(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Vector2') -> 'Vector2':
        return Vector2(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar: float) -> 'Vector2':
        return Vector2(self.x * scalar, self.y * scalar)
    
    def __truediv__(self, scalar: float) -> 'Vector2':
        return Vector2(self.x / scalar, self.y / scalar)
    
    def magnitude(self) -> float:
        """Get vector magnitude (length)"""
        return math.sqrt(self.x * self.x + self.y * self.y)
    
    def normalized(self) -> 'Vector2':
        """Get normalized vector"""
        mag = self.magnitude()
        if mag == 0:
            return Vector2(0, 0)
        return Vector2(self.x / mag, self.y / mag)
    
    def distance_to(self, other: 'Vector2') -> float:
        """Calculate distance to another vector"""
        return (self - other).magnitude()
    
    def dot(self, other: 'Vector2') -> float:
        """Dot product with another vector"""
        return self.x * other.x + self.y * other.y


@dataclass
class GridPosition:
    """Integer grid position for tile-based games"""
    x: int
    y: int
    
    def __add__(self, other: 'GridPosition') -> 'GridPosition':
        return GridPosition(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'GridPosition') -> 'GridPosition':
        return GridPosition(self.x - other.x, self.y - other.y)
    
    def __eq__(self, other) -> bool:
        return isinstance(other, GridPosition) and self.x == other.x and self.y == other.y
    
    def __hash__(self) -> int:
        return hash((self.x, self.y))
    
    def to_vector2(self) -> Vector2:
        """Convert to Vector2"""
        return Vector2(float(self.x), float(self.y))
    
    def manhattan_distance(self, other: 'GridPosition') -> int:
        """Calculate Manhattan distance"""
        return abs(self.x - other.x) + abs(self.y - other.y)
    
    def chebyshev_distance(self, other: 'GridPosition') -> int:
        """Calculate Chebyshev distance (chess king movement)"""
        return max(abs(self.x - other.x), abs(self.y - other.y))
    
    def euclidean_distance(self, other: 'GridPosition') -> float:
        """Calculate Euclidean distance"""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max"""
    return max(min_val, min(value, max_val))


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b"""
    return a + (b - a) * clamp(t, 0.0, 1.0)


def inverse_lerp(a: float, b: float, value: float) -> float:
    """Inverse linear interpolation"""
    if a == b:
        return 0.0
    return clamp((value - a) / (b - a), 0.0, 1.0)


def smooth_step(edge0: float, edge1: float, x: float) -> float:
    """Smooth interpolation with easing"""
    t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def angle_between_vectors(v1: Vector2, v2: Vector2) -> float:
    """Calculate angle between two vectors in radians"""
    dot_product = v1.dot(v2)
    magnitudes = v1.magnitude() * v2.magnitude()
    
    if magnitudes == 0:
        return 0.0
    
    cos_angle = clamp(dot_product / magnitudes, -1.0, 1.0)
    return math.acos(cos_angle)