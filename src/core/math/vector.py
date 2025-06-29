"""
Vector Mathematics for 3D Engine

Implements Vector3 and Vector2Int classes for spatial calculations.
All vector operations are immutable for thread safety and performance.
"""

import math
from typing import Dict, Any, Union

class Vector3:
    """
    Immutable 3D vector class for positions, directions, and scales.
    
    Provides standard vector operations with immutable semantics.
    Optimized for frequent calculations in tactical grid system.
    """
    
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self._x = float(x)
        self._y = float(y)
        self._z = float(z)
    
    @property
    def x(self) -> float:
        return self._x
    
    @property
    def y(self) -> float:
        return self._y
    
    @property
    def z(self) -> float:
        return self._z
    
    @property
    def magnitude(self) -> float:
        """Calculate vector magnitude (length)"""
        return math.sqrt(self._x * self._x + self._y * self._y + self._z * self._z)
    
    @property
    def magnitude_squared(self) -> float:
        """Calculate squared magnitude (faster for comparisons)"""
        return self._x * self._x + self._y * self._y + self._z * self._z
    
    @property
    def normalized(self) -> 'Vector3':
        """Return normalized vector (length = 1)"""
        mag = self.magnitude
        if mag == 0:
            return Vector3(0, 0, 0)
        return Vector3(self._x / mag, self._y / mag, self._z / mag)
    
    def __add__(self, other: 'Vector3') -> 'Vector3':
        """Vector addition"""
        return Vector3(self._x + other._x, self._y + other._y, self._z + other._z)
    
    def __sub__(self, other: 'Vector3') -> 'Vector3':
        """Vector subtraction"""
        return Vector3(self._x - other._x, self._y - other._y, self._z - other._z)
    
    def __mul__(self, scalar: float) -> 'Vector3':
        """Scalar multiplication"""
        return Vector3(self._x * scalar, self._y * scalar, self._z * scalar)
    
    def __rmul__(self, scalar: float) -> 'Vector3':
        """Reverse scalar multiplication"""
        return self.__mul__(scalar)
    
    def __truediv__(self, scalar: float) -> 'Vector3':
        """Scalar division"""
        if scalar == 0:
            raise ValueError("Cannot divide vector by zero")
        return Vector3(self._x / scalar, self._y / scalar, self._z / scalar)
    
    def __neg__(self) -> 'Vector3':
        """Vector negation"""
        return Vector3(-self._x, -self._y, -self._z)
    
    def __eq__(self, other: 'Vector3') -> bool:
        """Vector equality with floating point tolerance"""
        if not isinstance(other, Vector3):
            return False
        epsilon = 1e-6
        return (abs(self._x - other._x) < epsilon and 
                abs(self._y - other._y) < epsilon and 
                abs(self._z - other._z) < epsilon)
    
    def __str__(self) -> str:
        return f"Vector3({self._x:.3f}, {self._y:.3f}, {self._z:.3f})"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def dot(self, other: 'Vector3') -> float:
        """Dot product of two vectors"""
        return self._x * other._x + self._y * other._y + self._z * other._z
    
    def cross(self, other: 'Vector3') -> 'Vector3':
        """Cross product of two vectors"""
        return Vector3(
            self._y * other._z - self._z * other._y,
            self._z * other._x - self._x * other._z,
            self._x * other._y - self._y * other._x
        )
    
    def distance_to(self, other: 'Vector3') -> float:
        """Calculate distance to another vector"""
        return (self - other).magnitude
    
    def distance_squared_to(self, other: 'Vector3') -> float:
        """Calculate squared distance (faster for comparisons)"""
        return (self - other).magnitude_squared
    
    def lerp(self, other: 'Vector3', t: float) -> 'Vector3':
        """Linear interpolation between vectors"""
        t = max(0.0, min(1.0, t))  # Clamp t to [0, 1]
        return self + (other - self) * t
    
    def to_dict(self) -> Dict[str, float]:
        """Serialize to dictionary"""
        return {'x': self._x, 'y': self._y, 'z': self._z}
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'Vector3':
        """Deserialize from dictionary"""
        return cls(data['x'], data['y'], data['z'])
    
    # Common vector constants
    @classmethod
    def zero(cls) -> 'Vector3':
        return cls(0, 0, 0)
    
    @classmethod
    def one(cls) -> 'Vector3':
        return cls(1, 1, 1)
    
    @classmethod
    def up(cls) -> 'Vector3':
        return cls(0, 1, 0)
    
    @classmethod
    def down(cls) -> 'Vector3':
        return cls(0, -1, 0)
    
    @classmethod
    def forward(cls) -> 'Vector3':
        return cls(0, 0, 1)
    
    @classmethod
    def back(cls) -> 'Vector3':
        return cls(0, 0, -1)
    
    @classmethod
    def right(cls) -> 'Vector3':
        return cls(1, 0, 0)
    
    @classmethod
    def left(cls) -> 'Vector3':
        return cls(-1, 0, 0)

class Vector2Int:
    """
    Immutable 2D integer vector for grid coordinates.
    
    Used for tactical grid positions and array indices.
    Integer-only operations ensure exact grid alignment.
    """
    
    def __init__(self, x: int = 0, y: int = 0):
        self._x = int(x)
        self._y = int(y)
    
    @property
    def x(self) -> int:
        return self._x
    
    @property
    def y(self) -> int:
        return self._y
    
    @property
    def magnitude(self) -> float:
        """Calculate vector magnitude"""
        return math.sqrt(self._x * self._x + self._y * self._y)
    
    @property
    def magnitude_squared(self) -> int:
        """Calculate squared magnitude"""
        return self._x * self._x + self._y * self._y
    
    def __add__(self, other: 'Vector2Int') -> 'Vector2Int':
        """Vector addition"""
        return Vector2Int(self._x + other._x, self._y + other._y)
    
    def __sub__(self, other: 'Vector2Int') -> 'Vector2Int':
        """Vector subtraction"""
        return Vector2Int(self._x - other._x, self._y - other._y)
    
    def __mul__(self, scalar: int) -> 'Vector2Int':
        """Scalar multiplication"""
        return Vector2Int(self._x * scalar, self._y * scalar)
    
    def __rmul__(self, scalar: int) -> 'Vector2Int':
        """Reverse scalar multiplication"""
        return self.__mul__(scalar)
    
    def __neg__(self) -> 'Vector2Int':
        """Vector negation"""
        return Vector2Int(-self._x, -self._y)
    
    def __eq__(self, other: 'Vector2Int') -> bool:
        """Vector equality"""
        if not isinstance(other, Vector2Int):
            return False
        return self._x == other._x and self._y == other._y
    
    def __hash__(self) -> int:
        """Make hashable for use in sets/dicts"""
        return hash((self._x, self._y))
    
    def __str__(self) -> str:
        return f"Vector2Int({self._x}, {self._y})"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def manhattan_distance_to(self, other: 'Vector2Int') -> int:
        """Calculate Manhattan distance (grid distance)"""
        return abs(self._x - other._x) + abs(self._y - other._y)
    
    def to_dict(self) -> Dict[str, int]:
        """Serialize to dictionary"""
        return {'x': self._x, 'y': self._y}
    
    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'Vector2Int':
        """Deserialize from dictionary"""
        return cls(data['x'], data['y'])
    
    # Common vector constants
    @classmethod
    def zero(cls) -> 'Vector2Int':
        return cls(0, 0)
    
    @classmethod
    def one(cls) -> 'Vector2Int':
        return cls(1, 1)
    
    @classmethod
    def up(cls) -> 'Vector2Int':
        return cls(0, 1)
    
    @classmethod
    def down(cls) -> 'Vector2Int':
        return cls(0, -1)
    
    @classmethod
    def right(cls) -> 'Vector2Int':
        return cls(1, 0)
    
    @classmethod
    def left(cls) -> 'Vector2Int':
        return cls(-1, 0)
    
    # Cardinal directions for grid navigation
    @classmethod
    def cardinal_directions(cls) -> list['Vector2Int']:
        """Get all 4 cardinal directions"""
        return [cls.up(), cls.right(), cls.down(), cls.left()]
    
    @classmethod
    def diagonal_directions(cls) -> list['Vector2Int']:
        """Get all 4 diagonal directions"""
        return [
            cls(1, 1), cls(1, -1), 
            cls(-1, 1), cls(-1, -1)
        ]
    
    @classmethod
    def all_directions(cls) -> list['Vector2Int']:
        """Get all 8 directions (cardinal + diagonal)"""
        return cls.cardinal_directions() + cls.diagonal_directions()