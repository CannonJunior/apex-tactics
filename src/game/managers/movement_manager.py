"""
Movement Manager

Handles unit movement calculations, pathfinding, and movement execution.
Integrates with the pathfinding system and tactical grid.
"""

from typing import List, Optional, Tuple, Dict, Any
import math

from .base_manager import BaseManager
from game.interfaces.game_interfaces import IMovementManager
from core.models.unit import Unit
from core.math.pathfinding import AStarPathfinder
from core.math.grid import TacticalGrid, TerrainType
from core.math.vector import Vector2Int


class MovementManager(BaseManager, IMovementManager):
    """
    Manages unit movement, pathfinding, and movement validation.
    
    Features:
    - Pathfinding integration with A* algorithm
    - Movement range calculation
    - Movement validation and execution
    - Terrain and obstacle handling
    """
    
    def __init__(self, game_controller):
        super().__init__(game_controller)
        
        # Core pathfinding components
        self.tactical_grid = TacticalGrid(10, 8)  # Default 10x8 grid
        self.pathfinder = AStarPathfinder(self.tactical_grid)
        
        # Movement state
        self.movement_cache = {}  # Cache for movement range calculations
        self.movement_history = []  # Track movement for undo/replay
        
        # Performance tracking
        self.pathfinding_calls = 0
        self.cache_hits = 0
        
        print("✅ MovementManager initialized")
    
    def _perform_initialization(self):
        """Initialize movement manager."""
        # Update grid size if game controller has specific dimensions
        if hasattr(self.game_controller, 'grid_width') and hasattr(self.game_controller, 'grid_height'):
            self.tactical_grid = TacticalGrid(self.game_controller.grid_width, self.game_controller.grid_height)
            self.pathfinder = AStarPathfinder(self.tactical_grid)
        
        # Set up terrain and obstacles
        self._initialize_terrain()
        
        print("✅ MovementManager initialization complete")
    
    def _initialize_terrain(self):
        """Initialize terrain and obstacles on the grid."""
        # Set up basic terrain - this could be loaded from level data
        # For now, set all tiles as normal terrain (passable)
        for x in range(self.tactical_grid.width):
            for y in range(self.tactical_grid.height):
                grid_pos = Vector2Int(x, y)
                self.tactical_grid.set_cell_terrain(grid_pos, TerrainType.NORMAL)
        
        # Add obstacles based on game state
        if hasattr(self.game_controller, 'obstacles'):
            for obstacle in self.game_controller.obstacles:
                grid_pos = Vector2Int(obstacle.x, obstacle.y)
                self.tactical_grid.set_cell_terrain(grid_pos, TerrainType.WALL)
    
    def calculate_path(self, start: Tuple[int, int], end: Tuple[int, int], unit: Unit) -> Optional[List[Tuple[int, int]]]:
        """
        Calculate movement path from start to end position.
        
        Args:
            start: Starting position (x, y)
            end: Target position (x, y)
            unit: Unit that will move
            
        Returns:
            Path as list of (x, y) coordinates, or None if no path exists
        """
        self.pathfinding_calls += 1
        
        # Check if target is within movement range
        if not self._is_within_movement_range(start, end, unit):
            return None
        
        # Update grid with current unit positions
        self._update_grid_with_units(exclude_unit=unit)
        
        # Calculate path using A* pathfinder
        start_pos = Vector2Int(start[0], start[1])
        end_pos = Vector2Int(end[0], end[1])
        result = self.pathfinder.find_path(start_pos, end_pos)
        path = [(pos.x, pos.y) for pos in result.path] if result.success else None
        
        if path and len(path) > 1:
            # Remove starting position from path
            return path[1:]
        
        return None
    
    def validate_movement(self, unit: Unit, path: List[Tuple[int, int]]) -> bool:
        """
        Validate if a movement path is legal for a unit.
        
        Args:
            unit: Unit attempting to move
            path: Path to validate
            
        Returns:
            True if movement is valid
        """
        if not path:
            return False
        
        # Check if unit has enough movement points
        total_distance = len(path)
        if total_distance > unit.current_move_points:
            return False
        
        # Check if all tiles in path are passable
        for x, y in path:
            grid_pos = Vector2Int(x, y)
            cell = self.tactical_grid.get_cell(grid_pos)
            if not cell or not cell.passable or cell.occupied:
                return False
        
        # Check if path is continuous
        if not self._is_path_continuous([(unit.x, unit.y)] + path):
            return False
        
        return True
    
    def execute_movement(self, unit: Unit, path: List[Tuple[int, int]]) -> bool:
        """
        Execute unit movement along the specified path.
        
        Args:
            unit: Unit to move
            path: Path to move along
            
        Returns:
            True if movement was successful
        """
        if not self.validate_movement(unit, path):
            return False
        
        # Record movement for history
        old_position = (unit.x, unit.y)
        movement_record = {
            'unit_id': unit.name,
            'from': old_position,
            'path': path,
            'move_points_used': len(path)
        }
        
        # Execute the movement
        final_position = path[-1]
        unit.x, unit.y = final_position
        unit.current_move_points -= len(path)
        
        # Update movement history
        self.movement_history.append(movement_record)
        
        # Clear movement cache for this unit
        self._clear_movement_cache(unit)
        
        # Emit movement event
        if hasattr(self.game_controller, 'event_bus'):
            self.game_controller.event_bus.emit('unit_moved', {
                'unit': unit,
                'from': old_position,
                'to': final_position,
                'path': path
            })
        
        print(f"🚶 {unit.name} moved from {old_position} to {final_position}")
        return True
    
    def get_movement_range(self, unit: Unit) -> List[Tuple[int, int]]:
        """
        Get all valid movement positions for a unit.
        
        Args:
            unit: Unit to calculate movement range for
            
        Returns:
            List of (x, y) coordinates within movement range
        """
        # Check cache first
        cache_key = f"{unit.name}_{unit.x}_{unit.y}_{unit.current_move_points}"
        if cache_key in self.movement_cache:
            self.cache_hits += 1
            return self.movement_cache[cache_key]
        
        # Calculate movement range
        start_pos = (unit.x, unit.y)
        movement_range = []
        
        # Update grid with current unit positions
        self._update_grid_with_units(exclude_unit=unit)
        
        # Check all tiles within movement distance
        for x in range(max(0, unit.x - unit.current_move_points), 
                      min(self.tactical_grid.width, unit.x + unit.current_move_points + 1)):
            for y in range(max(0, unit.y - unit.current_move_points),
                          min(self.tactical_grid.height, unit.y + unit.current_move_points + 1)):
                
                # Skip current position
                if x == unit.x and y == unit.y:
                    continue
                
                # Check if tile is reachable
                if self._is_tile_reachable(start_pos, (x, y), unit.current_move_points):
                    movement_range.append((x, y))
        
        # Cache the result
        self.movement_cache[cache_key] = movement_range
        
        return movement_range
    
    def _is_within_movement_range(self, start: Tuple[int, int], end: Tuple[int, int], unit: Unit) -> bool:
        """Check if target position is within unit's movement range."""
        distance = abs(end[0] - start[0]) + abs(end[1] - start[1])  # Manhattan distance
        return distance <= unit.current_move_points
    
    def _update_grid_with_units(self, exclude_unit: Optional[Unit] = None):
        """Update grid with current unit positions."""
        # Free all occupied cells first
        for x in range(self.tactical_grid.width):
            for y in range(self.tactical_grid.height):
                grid_pos = Vector2Int(x, y)
                self.tactical_grid.free_cell(grid_pos)
        
        # Re-add terrain obstacles  
        if hasattr(self.game_controller, 'obstacles'):
            for obstacle in self.game_controller.obstacles:
                grid_pos = Vector2Int(obstacle.x, obstacle.y)
                self.tactical_grid.set_cell_terrain(grid_pos, TerrainType.WALL)
        
        # Add unit positions as occupied
        if hasattr(self.game_controller, 'units'):
            for unit in self.game_controller.units:
                if unit != exclude_unit:
                    grid_pos = Vector2Int(unit.x, unit.y)
                    self.tactical_grid.occupy_cell(grid_pos, unit.name)
    
    def _is_tile_occupied(self, x: int, y: int, exclude_unit: Optional[Unit] = None) -> bool:
        """Check if a tile is occupied by a unit."""
        if hasattr(self.game_controller, 'units'):
            for unit in self.game_controller.units:
                if unit != exclude_unit and unit.x == x and unit.y == y:
                    return True
        return False
    
    def _is_path_continuous(self, path: List[Tuple[int, int]]) -> bool:
        """Check if path has no gaps (adjacent tiles only)."""
        for i in range(len(path) - 1):
            curr_x, curr_y = path[i]
            next_x, next_y = path[i + 1]
            
            # Check if next tile is adjacent (Manhattan distance = 1)
            if abs(next_x - curr_x) + abs(next_y - curr_y) != 1:
                return False
        
        return True
    
    def _is_tile_reachable(self, start: Tuple[int, int], target: Tuple[int, int], max_distance: int) -> bool:
        """Check if a tile is reachable within the movement distance."""
        # Simple check - use pathfinding to verify
        start_pos = Vector2Int(start[0], start[1])
        target_pos = Vector2Int(target[0], target[1])
        result = self.pathfinder.find_path(start_pos, target_pos)
        return result.success and len(result.path) <= max_distance + 1
    
    def _clear_movement_cache(self, unit: Unit):
        """Clear movement cache entries for a specific unit."""
        keys_to_remove = [key for key in self.movement_cache.keys() if key.startswith(f"{unit.name}_")]
        for key in keys_to_remove:
            del self.movement_cache[key]
    
    def get_movement_cost(self, start: Tuple[int, int], end: Tuple[int, int]) -> int:
        """Get the movement cost between two positions."""
        start_pos = Vector2Int(start[0], start[1])
        end_pos = Vector2Int(end[0], end[1])
        result = self.pathfinder.find_path(start_pos, end_pos)
        return len(result.path) - 1 if result.success else float('inf')
    
    def can_unit_move_to(self, unit: Unit, target: Tuple[int, int]) -> bool:
        """Check if a unit can move to a specific position."""
        grid_pos = Vector2Int(target[0], target[1])
        cell = self.tactical_grid.get_cell(grid_pos)
        
        if not cell or not cell.passable:
            return False
        
        if self._is_tile_occupied(target[0], target[1], exclude_unit=unit):
            return False
        
        path = self.calculate_path((unit.x, unit.y), target, unit)
        return path is not None
    
    def get_movement_stats(self) -> Dict[str, Any]:
        """Get movement system performance statistics."""
        return {
            'pathfinding_calls': self.pathfinding_calls,
            'cache_hits': self.cache_hits,
            'cache_hit_rate': self.cache_hits / max(1, self.pathfinding_calls),
            'cached_ranges': len(self.movement_cache),
            'movement_history': len(self.movement_history)
        }
    
    def reset_movement_points(self, unit: Unit):
        """Reset unit's movement points to maximum."""
        unit.current_move_points = getattr(unit, 'max_move_points', getattr(unit, 'move_points', 3))
        self._clear_movement_cache(unit)
    
    def shutdown(self):
        """Shutdown movement manager."""
        self.movement_cache.clear()
        self.movement_history.clear()
        print("✅ MovementManager shutdown complete")