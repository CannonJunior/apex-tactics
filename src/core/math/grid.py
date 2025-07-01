"""
Grid System with Height Variations

Implements tactical grid system supporting height variations and movement costs.
Optimized for <2ms pathfinding queries on 10x10 grids per performance targets.
"""

import math
from typing import Dict, List, Optional, Tuple, Set, Callable
from enum import Enum

from .vector import Vector3, Vector2Int

class TerrainType(Enum):
    """Terrain type enumeration for movement and tactical calculations"""
    NORMAL = "normal"
    DIFFICULT = "difficult"
    WATER = "water"
    WALL = "wall"
    PIT = "pit"
    ELEVATED = "elevated"

class GridCell:
    """
    Individual grid cell with height and terrain properties.
    
    Contains all data needed for tactical calculations and pathfinding.
    """
    
    def __init__(self, grid_pos: Vector2Int, height: float = 0.0, 
                 terrain_type: TerrainType = TerrainType.NORMAL):
        self.grid_pos = grid_pos
        self.height = height
        self.terrain_type = terrain_type
        self.passable = terrain_type != TerrainType.WALL
        self.occupied = False
        self.occupant_id: Optional[str] = None
        
        # Movement costs for different terrain types
        self._movement_costs = {
            TerrainType.NORMAL: 1.0,
            TerrainType.DIFFICULT: 2.0,
            TerrainType.WATER: 1.5,
            TerrainType.WALL: float('inf'),
            TerrainType.PIT: 3.0,
            TerrainType.ELEVATED: 1.2
        }
    
    @property
    def movement_cost(self) -> float:
        """Get base movement cost for this cell"""
        return self._movement_costs.get(self.terrain_type, 1.0)
    
    @property
    def world_position(self) -> Vector3:
        """Get 3D world position of cell center"""
        return Vector3(
            float(self.grid_pos.x),
            self.height,
            float(self.grid_pos.y)
        )
    
    def get_height_difference_cost(self, other_cell: 'GridCell') -> float:
        """
        Calculate additional movement cost due to height difference.
        
        Args:
            other_cell: Target cell to move to
            
        Returns:
            Additional movement cost multiplier
        """
        height_diff = abs(self.height - other_cell.height)
        
        # Exponential cost increase for height differences
        if height_diff <= 0.5:
            return 0.0  # No penalty for small height differences
        elif height_diff <= 1.0:
            return 0.5  # Small penalty
        elif height_diff <= 2.0:
            return 1.0  # Moderate penalty
        else:
            return 2.0  # High penalty for large height differences
    
    def can_move_to(self, other_cell: 'GridCell', max_height_diff: float = 2.0) -> bool:
        """
        Check if movement to another cell is possible.
        
        Args:
            other_cell: Target cell
            max_height_diff: Maximum allowed height difference
            
        Returns:
            True if movement is possible
        """
        if not other_cell.passable or other_cell.occupied:
            return False
        
        height_diff = abs(self.height - other_cell.height)
        return height_diff <= max_height_diff
    
    def to_dict(self) -> Dict[str, any]:
        """Serialize cell to dictionary"""
        return {
            'grid_pos': self.grid_pos.to_dict(),
            'height': self.height,
            'terrain_type': self.terrain_type.value,
            'passable': self.passable,
            'occupied': self.occupied,
            'occupant_id': self.occupant_id
        }

class TacticalGrid:
    """
    Main grid system for tactical combat.
    
    Manages grid cells, height variations, and provides pathfinding support.
    Optimized for performance with 10x10+ grids.
    """
    
    def __init__(self, width: int, height: int, cell_size: float = 1.0):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        
        # Initialize grid with normal terrain at height 0
        self.cells: Dict[Vector2Int, GridCell] = {}
        for x in range(width):
            for y in range(height):
                grid_pos = Vector2Int(x, y)
                self.cells[grid_pos] = GridCell(grid_pos)
        
        # Cache for pathfinding optimization
        self._pathfinding_cache: Dict[Tuple[Vector2Int, Vector2Int], List[Vector2Int]] = {}
        self._cache_max_size = 1000
        
        # Pre-compute neighbor relationships for performance
        self._neighbor_cache: Dict[Vector2Int, List[Vector2Int]] = {}
        self._diagonal_neighbor_cache: Dict[Vector2Int, List[Vector2Int]] = {}
        self._precompute_neighbors()
    
    def get_cell(self, grid_pos: Vector2Int) -> Optional[GridCell]:
        """
        Get cell at grid position.
        
        Args:
            grid_pos: Grid coordinates
            
        Returns:
            GridCell or None if position is invalid
        """
        return self.cells.get(grid_pos)
    
    def set_cell_height(self, grid_pos: Vector2Int, height: float):
        """
        Set height of cell at position.
        
        Args:
            grid_pos: Grid coordinates
            height: New height value
        """
        cell = self.get_cell(grid_pos)
        if cell:
            cell.height = height
            self._invalidate_pathfinding_cache()
    
    def set_cell_terrain(self, grid_pos: Vector2Int, terrain_type: TerrainType):
        """
        Set terrain type of cell at position.
        
        Args:
            grid_pos: Grid coordinates
            terrain_type: New terrain type
        """
        cell = self.get_cell(grid_pos)
        if cell:
            cell.terrain_type = terrain_type
            cell.passable = terrain_type != TerrainType.WALL
            self._invalidate_pathfinding_cache()
    
    def occupy_cell(self, grid_pos: Vector2Int, occupant_id: str) -> bool:
        """
        Mark cell as occupied by entity.
        
        Args:
            grid_pos: Grid coordinates
            occupant_id: ID of occupying entity
            
        Returns:
            True if cell was successfully occupied
        """
        cell = self.get_cell(grid_pos)
        if cell and not cell.occupied and cell.passable:
            cell.occupied = True
            cell.occupant_id = occupant_id
            return True
        return False
    
    def free_cell(self, grid_pos: Vector2Int) -> bool:
        """
        Mark cell as unoccupied.
        
        Args:
            grid_pos: Grid coordinates
            
        Returns:
            True if cell was freed
        """
        cell = self.get_cell(grid_pos)
        if cell and cell.occupied:
            cell.occupied = False
            cell.occupant_id = None
            return True
        return False
    
    def world_to_grid(self, world_pos: Vector3) -> Vector2Int:
        """
        Convert world position to grid coordinates.
        
        Args:
            world_pos: World position
            
        Returns:
            Grid coordinates
        """
        grid_x = int(world_pos.x / self.cell_size)
        grid_y = int(world_pos.z / self.cell_size)
        return Vector2Int(grid_x, grid_y)
    
    def grid_to_world(self, grid_pos: Vector2Int) -> Vector3:
        """
        Convert grid coordinates to world position.
        
        Args:
            grid_pos: Grid coordinates
            
        Returns:
            World position at cell center with height
        """
        cell = self.get_cell(grid_pos)
        height = cell.height if cell else 0.0
        
        world_x = (grid_pos.x + 0.5) * self.cell_size
        world_z = (grid_pos.y + 0.5) * self.cell_size
        
        return Vector3(world_x, height, world_z)
    
    def is_valid_position(self, grid_pos: Vector2Int) -> bool:
        """
        Check if grid position is within bounds.
        
        Args:
            grid_pos: Grid coordinates to check
            
        Returns:
            True if position is valid
        """
        return (0 <= grid_pos.x < self.width and 
                0 <= grid_pos.y < self.height)
    
    def get_neighbors(self, grid_pos: Vector2Int, 
                     include_diagonals: bool = True) -> List[Vector2Int]:
        """
        Get neighboring grid positions using pre-computed cache.
        
        Args:
            grid_pos: Center position
            include_diagonals: Whether to include diagonal neighbors
            
        Returns:
            List of valid neighboring positions
        """
        # Use pre-computed neighbor cache for better performance
        if include_diagonals:
            return self._diagonal_neighbor_cache.get(grid_pos, [])
        else:
            return self._neighbor_cache.get(grid_pos, [])
    
    def get_movement_cost(self, from_pos: Vector2Int, to_pos: Vector2Int) -> float:
        """
        Calculate movement cost between adjacent cells.
        
        Args:
            from_pos: Starting position
            to_pos: Target position
            
        Returns:
            Movement cost (float('inf') if movement impossible)
        """
        from_cell = self.get_cell(from_pos)
        to_cell = self.get_cell(to_pos)
        
        if not from_cell or not to_cell:
            return float('inf')
        
        if not from_cell.can_move_to(to_cell):
            return float('inf')
        
        # Base cost from terrain
        base_cost = to_cell.movement_cost
        
        # Additional cost from height difference
        height_cost = from_cell.get_height_difference_cost(to_cell)
        
        # Diagonal movement costs more
        distance = from_pos.manhattan_distance_to(to_pos)
        diagonal_multiplier = 1.414 if distance > 1 else 1.0
        
        return (base_cost + height_cost) * diagonal_multiplier
    
    def get_line_of_sight(self, from_pos: Vector2Int, to_pos: Vector2Int) -> bool:
        """
        Check if there is line of sight between two positions.
        
        Args:
            from_pos: Starting position
            to_pos: Target position
            
        Returns:
            True if line of sight exists
        """
        from_cell = self.get_cell(from_pos)
        to_cell = self.get_cell(to_pos)
        
        if not from_cell or not to_cell:
            return False
        
        # Use Bresenham's line algorithm to check cells between positions
        cells_on_line = self._get_line_cells(from_pos, to_pos)
        
        from_height = from_cell.height + 1.5  # Eye level
        to_height = to_cell.height + 1.5
        
        for i, cell_pos in enumerate(cells_on_line[1:-1], 1):  # Skip start and end
            cell = self.get_cell(cell_pos)
            if not cell:
                continue
            
            # Calculate expected height at this point on the line
            progress = i / len(cells_on_line)
            expected_height = from_height + (to_height - from_height) * progress
            
            # Check if terrain blocks the line
            if cell.height > expected_height - 0.5:  # Allow some clearance
                return False
        
        return True
    
    def _get_line_cells(self, from_pos: Vector2Int, to_pos: Vector2Int) -> List[Vector2Int]:
        """Get all cells on line between two positions using Bresenham's algorithm"""
        cells = []
        
        x0, y0 = from_pos.x, from_pos.y
        x1, y1 = to_pos.x, to_pos.y
        
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        
        x_step = 1 if x0 < x1 else -1
        y_step = 1 if y0 < y1 else -1
        
        error = dx - dy
        
        x, y = x0, y0
        
        while True:
            cells.append(Vector2Int(x, y))
            
            if x == x1 and y == y1:
                break
            
            error2 = 2 * error
            
            if error2 > -dy:
                error -= dy
                x += x_step
            
            if error2 < dx:
                error += dx
                y += y_step
        
        return cells
    
    def get_cells_in_range(self, center: Vector2Int, 
                          range_distance: int) -> List[Vector2Int]:
        """
        Get all cells within specified range.
        
        Args:
            center: Center position
            range_distance: Maximum distance (Manhattan)
            
        Returns:
            List of positions within range
        """
        cells_in_range = []
        
        for x in range(max(0, center.x - range_distance),
                      min(self.width, center.x + range_distance + 1)):
            for y in range(max(0, center.y - range_distance),
                          min(self.height, center.y + range_distance + 1)):
                pos = Vector2Int(x, y)
                
                if pos.manhattan_distance_to(center) <= range_distance:
                    cells_in_range.append(pos)
        
        return cells_in_range
    
    def _invalidate_pathfinding_cache(self):
        """Clear pathfinding cache when grid changes"""
        self._pathfinding_cache.clear()
    
    def _precompute_neighbors(self):
        """Pre-compute neighbor relationships for all grid positions"""
        for x in range(self.width):
            for y in range(self.height):
                grid_pos = Vector2Int(x, y)
                
                # Compute neighbors without diagonals
                neighbors = []
                diagonal_neighbors = []
                
                # Cardinal directions
                directions = [
                    Vector2Int(0, 1),   # North
                    Vector2Int(1, 0),   # East  
                    Vector2Int(0, -1),  # South
                    Vector2Int(-1, 0)   # West
                ]
                
                for direction in directions:
                    neighbor_pos = grid_pos + direction
                    if (0 <= neighbor_pos.x < self.width and 
                        0 <= neighbor_pos.y < self.height):
                        neighbors.append(neighbor_pos)
                        diagonal_neighbors.append(neighbor_pos)
                
                # Diagonal directions
                diagonal_dirs = [
                    Vector2Int(1, 1),   # Northeast
                    Vector2Int(1, -1),  # Southeast
                    Vector2Int(-1, -1), # Southwest
                    Vector2Int(-1, 1)   # Northwest
                ]
                
                for direction in diagonal_dirs:
                    neighbor_pos = grid_pos + direction
                    if (0 <= neighbor_pos.x < self.width and 
                        0 <= neighbor_pos.y < self.height):
                        diagonal_neighbors.append(neighbor_pos)
                
                self._neighbor_cache[grid_pos] = neighbors
                self._diagonal_neighbor_cache[grid_pos] = diagonal_neighbors
    
    def generate_height_map(self, seed: int = 42, roughness: float = 0.5):
        """
        Generate height variations using simple noise.
        
        Args:
            seed: Random seed for reproducible generation
            roughness: Amount of height variation (0.0 to 1.0)
        """
        import random
        random.seed(seed)
        
        # Simple height generation with smoothing
        for grid_pos, cell in self.cells.items():
            # Generate base height with some randomness
            noise_value = random.random() * 2 - 1  # -1 to 1
            base_height = noise_value * roughness * 3.0
            
            # Smooth based on neighbors
            neighbor_heights = []
            for neighbor_pos in self.get_neighbors(grid_pos, False):
                neighbor_cell = self.get_cell(neighbor_pos)
                if neighbor_cell and hasattr(neighbor_cell, '_temp_height'):
                    neighbor_heights.append(neighbor_cell._temp_height)
            
            if neighbor_heights:
                avg_neighbor_height = sum(neighbor_heights) / len(neighbor_heights)
                final_height = (base_height + avg_neighbor_height * 0.5) / 1.5
            else:
                final_height = base_height
            
            cell._temp_height = final_height
        
        # Apply the heights
        for cell in self.cells.values():
            cell.height = cell._temp_height
            delattr(cell, '_temp_height')
        
        self._invalidate_pathfinding_cache()
    
    def to_dict(self) -> Dict[str, any]:
        """Serialize grid to dictionary"""
        return {
            'width': self.width,
            'height': self.height,
            'cell_size': self.cell_size,
            'cells': {
                f"{pos.x},{pos.y}": cell.to_dict()
                for pos, cell in self.cells.items()
            }
        }