"""
Math Utilities

Mathematical operations for 3D vectors, grid coordinates, and spatial calculations.
"""

from .vector import Vector3, Vector2Int
from .grid import TacticalGrid, GridCell, TerrainType
from .pathfinding import AStarPathfinder, PathfindingResult, JumpPointSearch

# Aliases for backward compatibility
Vector2 = Vector2Int
GridPosition = Vector2Int

# Utility functions
def clamp(value, min_val, max_val):
    """Clamp value between min and max"""
    return max(min_val, min(value, max_val))

__all__ = [
    'Vector3', 'Vector2Int', 'Vector2', 'GridPosition',
    'TacticalGrid', 'GridCell', 'TerrainType',
    'AStarPathfinder', 'PathfindingResult', 'JumpPointSearch',
    'clamp'
]