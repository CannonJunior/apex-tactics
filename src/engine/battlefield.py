"""
Battlefield Management System

Handles battlefield grid, terrain, pathfinding, and spatial queries
for tactical combat gameplay.
"""

import asyncio
import heapq
import math
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

import structlog
import numpy as np

from ..core.math import Vector2, GridPosition
from ..core.ecs import EntityID

logger = structlog.get_logger()


class TerrainType(str, Enum):
    """Terrain types with movement and combat effects"""
    PLAINS = "plains"
    FOREST = "forest"
    MOUNTAINS = "mountains"
    WATER = "water"
    WALLS = "walls"
    ROUGH = "rough"
    ROAD = "road"


class TileStatus(str, Enum):
    """Tile occupation status"""
    EMPTY = "empty"
    OCCUPIED = "occupied"
    BLOCKED = "blocked"
    OBJECTIVE = "objective"


@dataclass
class TerrainProperties:
    """Properties for different terrain types"""
    movement_cost: float = 1.0
    defense_bonus: float = 0.0
    accuracy_modifier: float = 0.0
    blocks_vision: bool = False
    blocks_movement: bool = False
    can_fly_over: bool = True
    description: str = ""


@dataclass
class BattlefieldTile:
    """Individual battlefield tile"""
    position: GridPosition
    terrain_type: TerrainType = TerrainType.PLAINS
    status: TileStatus = TileStatus.EMPTY
    occupant: Optional[EntityID] = None
    height: float = 0.0
    visible_to_teams: Set[str] = field(default_factory=set)
    
    # Visual and gameplay properties
    highlight: Optional[str] = None  # "move", "attack", "selected", etc.
    effects: List[str] = field(default_factory=list)  # Status effects on tile
    
    def is_passable(self, terrain_properties: Dict[TerrainType, TerrainProperties]) -> bool:
        """Check if tile is passable"""
        if self.status == TileStatus.BLOCKED:
            return False
        
        if self.status == TileStatus.OCCUPIED:
            return False
        
        terrain_props = terrain_properties.get(self.terrain_type)
        if terrain_props and terrain_props.blocks_movement:
            return False
        
        return True
    
    def get_movement_cost(self, terrain_properties: Dict[TerrainType, TerrainProperties]) -> float:
        """Get movement cost for this tile"""
        terrain_props = terrain_properties.get(self.terrain_type)
        if terrain_props:
            return terrain_props.movement_cost
        return 1.0


@dataclass
class PathfindingNode:
    """Node for A* pathfinding"""
    position: GridPosition
    g_cost: float = 0.0  # Distance from start
    h_cost: float = 0.0  # Heuristic distance to goal
    parent: Optional['PathfindingNode'] = None
    
    @property
    def f_cost(self) -> float:
        """Total cost (g + h)"""
        return self.g_cost + self.h_cost
    
    def __lt__(self, other):
        return self.f_cost < other.f_cost


class BattlefieldManager:
    """Manages battlefield grid, terrain, and pathfinding"""
    
    def __init__(self, size: Tuple[int, int] = (10, 10)):
        self.size = size
        self.width, self.height = size
        
        # Battlefield data per session
        self.battlefields: Dict[str, Dict[Tuple[int, int], BattlefieldTile]] = {}
        self.terrain_properties = self._initialize_terrain_properties()
        
        # Pathfinding cache
        self.pathfinding_cache: Dict[str, Dict[Tuple[Tuple[int, int], Tuple[int, int]], List[GridPosition]]] = {}
        
        # Performance tracking
        self.pathfinding_calls = 0
        self.cache_hits = 0
        
        logger.info("Battlefield manager initialized", size=size)
    
    def _initialize_terrain_properties(self) -> Dict[TerrainType, TerrainProperties]:
        """Initialize terrain type properties"""
        return {
            TerrainType.PLAINS: TerrainProperties(
                movement_cost=1.0,
                defense_bonus=0.0,
                accuracy_modifier=0.0,
                description="Open plains with no special effects"
            ),
            TerrainType.FOREST: TerrainProperties(
                movement_cost=1.5,
                defense_bonus=0.2,
                accuracy_modifier=-0.1,
                blocks_vision=True,
                description="Dense forest providing cover but hindering movement"
            ),
            TerrainType.MOUNTAINS: TerrainProperties(
                movement_cost=2.0,
                defense_bonus=0.3,
                accuracy_modifier=0.1,
                description="High ground with defensive advantage"
            ),
            TerrainType.WATER: TerrainProperties(
                movement_cost=3.0,
                defense_bonus=-0.1,
                accuracy_modifier=-0.2,
                description="Deep water slowing movement"
            ),
            TerrainType.WALLS: TerrainProperties(
                movement_cost=float('inf'),
                blocks_movement=True,
                blocks_vision=True,
                can_fly_over=False,
                description="Impassable walls"
            ),
            TerrainType.ROUGH: TerrainProperties(
                movement_cost=1.3,
                defense_bonus=0.1,
                accuracy_modifier=-0.05,
                description="Rough terrain with minor penalties"
            ),
            TerrainType.ROAD: TerrainProperties(
                movement_cost=0.8,
                defense_bonus=-0.1,
                accuracy_modifier=0.0,
                description="Well-maintained roads for fast movement"
            )
        }
    
    async def initialize_for_session(self, session_id: str, size: Optional[Tuple[int, int]] = None):
        """Initialize battlefield for a game session"""
        if size:
            self.size = size
            self.width, self.height = size
        
        # Create empty battlefield
        battlefield = {}
        for x in range(self.width):
            for y in range(self.height):
                position = GridPosition(x, y)
                battlefield[(x, y)] = BattlefieldTile(position=position)
        
        self.battlefields[session_id] = battlefield
        self.pathfinding_cache[session_id] = {}
        
        logger.info("Battlefield initialized for session", 
                   session_id=session_id, 
                   size=self.size)
    
    def get_tile(self, session_id: str, position: GridPosition) -> Optional[BattlefieldTile]:
        """Get tile at position"""
        if session_id not in self.battlefields:
            return None
        
        battlefield = self.battlefields[session_id]
        return battlefield.get((position.x, position.y))
    
    def set_tile_terrain(self, session_id: str, position: GridPosition, terrain_type: TerrainType):
        """Set terrain type for a tile"""
        tile = self.get_tile(session_id, position)
        if tile:
            tile.terrain_type = terrain_type
            self._invalidate_pathfinding_cache(session_id)
    
    def set_tile_height(self, session_id: str, position: GridPosition, height: float):
        """Set height for a tile"""
        tile = self.get_tile(session_id, position)
        if tile:
            tile.height = height
    
    def occupy_tile(self, session_id: str, position: GridPosition, entity_id: EntityID) -> bool:
        """Occupy a tile with an entity"""
        tile = self.get_tile(session_id, position)
        if not tile:
            return False
        
        if tile.status == TileStatus.OCCUPIED:
            return False
        
        tile.status = TileStatus.OCCUPIED
        tile.occupant = entity_id
        self._invalidate_pathfinding_cache(session_id)
        
        logger.debug("Tile occupied", 
                    session_id=session_id, 
                    position=position.__dict__, 
                    entity_id=str(entity_id))
        return True
    
    def vacate_tile(self, session_id: str, position: GridPosition) -> bool:
        """Vacate a tile"""
        tile = self.get_tile(session_id, position)
        if not tile:
            return False
        
        if tile.status == TileStatus.OCCUPIED:
            tile.status = TileStatus.EMPTY
            tile.occupant = None
            self._invalidate_pathfinding_cache(session_id)
            
            logger.debug("Tile vacated", 
                        session_id=session_id, 
                        position=position.__dict__)
            return True
        
        return False
    
    def get_occupant(self, session_id: str, position: GridPosition) -> Optional[EntityID]:
        """Get entity occupying a tile"""
        tile = self.get_tile(session_id, position)
        return tile.occupant if tile else None
    
    def is_position_valid(self, position: GridPosition) -> bool:
        """Check if position is within battlefield bounds"""
        return (0 <= position.x < self.width and 
                0 <= position.y < self.height)
    
    def is_tile_passable(self, session_id: str, position: GridPosition, 
                        ignore_occupants: bool = False) -> bool:
        """Check if tile is passable"""
        if not self.is_position_valid(position):
            return False
        
        tile = self.get_tile(session_id, position)
        if not tile:
            return False
        
        if not ignore_occupants and tile.status == TileStatus.OCCUPIED:
            return False
        
        return tile.is_passable(self.terrain_properties)
    
    def get_neighbors(self, position: GridPosition, include_diagonals: bool = True) -> List[GridPosition]:
        """Get neighboring positions"""
        neighbors = []
        directions = [
            (0, 1), (1, 0), (0, -1), (-1, 0)  # Cardinal directions
        ]
        
        if include_diagonals:
            directions.extend([
                (1, 1), (1, -1), (-1, 1), (-1, -1)  # Diagonal directions
            ])
        
        for dx, dy in directions:
            new_pos = GridPosition(position.x + dx, position.y + dy)
            if self.is_position_valid(new_pos):
                neighbors.append(new_pos)
        
        return neighbors
    
    def calculate_distance(self, pos1: GridPosition, pos2: GridPosition, 
                          distance_type: str = "manhattan") -> float:
        """Calculate distance between positions"""
        if distance_type == "manhattan":
            return abs(pos1.x - pos2.x) + abs(pos1.y - pos2.y)
        elif distance_type == "euclidean":
            return math.sqrt((pos1.x - pos2.x) ** 2 + (pos1.y - pos2.y) ** 2)
        elif distance_type == "chebyshev":
            return max(abs(pos1.x - pos2.x), abs(pos1.y - pos2.y))
        else:
            return abs(pos1.x - pos2.x) + abs(pos1.y - pos2.y)  # Default to Manhattan
    
    async def find_path(self, session_id: str, start: GridPosition, goal: GridPosition,
                       ignore_occupants: bool = False, max_range: Optional[int] = None) -> List[GridPosition]:
        """Find path using A* algorithm"""
        self.pathfinding_calls += 1
        
        # Check cache first
        cache_key = ((start.x, start.y), (goal.x, goal.y))
        if session_id in self.pathfinding_cache:
            cached_path = self.pathfinding_cache[session_id].get(cache_key)
            if cached_path:
                self.cache_hits += 1
                return cached_path
        
        # Validate start and goal
        if not (self.is_position_valid(start) and self.is_position_valid(goal)):
            return []
        
        if not self.is_tile_passable(session_id, goal, ignore_occupants):
            return []
        
        # A* pathfinding
        open_set = []
        closed_set = set()
        nodes = {}
        
        start_node = PathfindingNode(start)
        start_node.h_cost = self.calculate_distance(start, goal)
        nodes[(start.x, start.y)] = start_node
        heapq.heappush(open_set, start_node)
        
        while open_set:
            current_node = heapq.heappop(open_set)
            current_pos = current_node.position
            
            if (current_pos.x, current_pos.y) in closed_set:
                continue
            
            closed_set.add((current_pos.x, current_pos.y))
            
            # Check if we reached the goal
            if current_pos.x == goal.x and current_pos.y == goal.y:
                path = self._reconstruct_path(current_node)
                
                # Cache the result
                if session_id not in self.pathfinding_cache:
                    self.pathfinding_cache[session_id] = {}
                self.pathfinding_cache[session_id][cache_key] = path
                
                return path
            
            # Check range limit
            if max_range and current_node.g_cost >= max_range:
                continue
            
            # Explore neighbors
            for neighbor_pos in self.get_neighbors(current_pos):
                if (neighbor_pos.x, neighbor_pos.y) in closed_set:
                    continue
                
                if not self.is_tile_passable(session_id, neighbor_pos, ignore_occupants):
                    continue
                
                # Calculate movement cost
                tile = self.get_tile(session_id, neighbor_pos)
                movement_cost = tile.get_movement_cost(self.terrain_properties) if tile else 1.0
                
                # Add diagonal movement cost
                if abs(neighbor_pos.x - current_pos.x) + abs(neighbor_pos.y - current_pos.y) > 1:
                    movement_cost *= 1.414  # sqrt(2) for diagonal movement
                
                tentative_g_cost = current_node.g_cost + movement_cost
                
                neighbor_key = (neighbor_pos.x, neighbor_pos.y)
                if neighbor_key not in nodes:
                    nodes[neighbor_key] = PathfindingNode(neighbor_pos)
                
                neighbor_node = nodes[neighbor_key]
                
                if tentative_g_cost < neighbor_node.g_cost or neighbor_node.g_cost == 0:
                    neighbor_node.parent = current_node
                    neighbor_node.g_cost = tentative_g_cost
                    neighbor_node.h_cost = self.calculate_distance(neighbor_pos, goal)
                    
                    heapq.heappush(open_set, neighbor_node)
        
        # No path found
        return []
    
    def _reconstruct_path(self, end_node: PathfindingNode) -> List[GridPosition]:
        """Reconstruct path from pathfinding nodes"""
        path = []
        current = end_node
        
        while current:
            path.append(current.position)
            current = current.parent
        
        path.reverse()
        return path
    
    def get_reachable_tiles(self, session_id: str, start: GridPosition, 
                           max_movement: float, ignore_occupants: bool = False) -> List[GridPosition]:
        """Get all tiles reachable within movement range"""
        reachable = []
        visited = set()
        queue = [(start, 0.0)]  # (position, movement_cost)
        
        while queue:
            current_pos, current_cost = queue.pop(0)
            pos_key = (current_pos.x, current_pos.y)
            
            if pos_key in visited:
                continue
            
            visited.add(pos_key)
            reachable.append(current_pos)
            
            # Explore neighbors
            for neighbor_pos in self.get_neighbors(current_pos):
                if (neighbor_pos.x, neighbor_pos.y) in visited:
                    continue
                
                if not self.is_tile_passable(session_id, neighbor_pos, ignore_occupants):
                    continue
                
                tile = self.get_tile(session_id, neighbor_pos)
                movement_cost = tile.get_movement_cost(self.terrain_properties) if tile else 1.0
                
                # Add diagonal cost
                if abs(neighbor_pos.x - current_pos.x) + abs(neighbor_pos.y - current_pos.y) > 1:
                    movement_cost *= 1.414
                
                new_cost = current_cost + movement_cost
                
                if new_cost <= max_movement:
                    queue.append((neighbor_pos, new_cost))
        
        return reachable
    
    def get_tiles_in_range(self, center: GridPosition, range_value: int, 
                          range_type: str = "manhattan") -> List[GridPosition]:
        """Get all tiles within range of center position"""
        tiles = []
        
        for x in range(max(0, center.x - range_value), 
                      min(self.width, center.x + range_value + 1)):
            for y in range(max(0, center.y - range_value), 
                          min(self.height, center.y + range_value + 1)):
                pos = GridPosition(x, y)
                distance = self.calculate_distance(center, pos, range_type)
                
                if distance <= range_value:
                    tiles.append(pos)
        
        return tiles
    
    def has_line_of_sight(self, session_id: str, start: GridPosition, 
                         end: GridPosition) -> bool:
        """Check if there's line of sight between two positions"""
        # Bresenham's line algorithm to check each tile in the line
        positions = self._get_line_positions(start, end)
        
        for pos in positions[1:-1]:  # Skip start and end positions
            tile = self.get_tile(session_id, pos)
            if tile:
                terrain_props = self.terrain_properties.get(tile.terrain_type)
                if terrain_props and terrain_props.blocks_vision:
                    return False
        
        return True
    
    def _get_line_positions(self, start: GridPosition, end: GridPosition) -> List[GridPosition]:
        """Get positions along a line using Bresenham's algorithm"""
        positions = []
        
        x0, y0 = start.x, start.y
        x1, y1 = end.x, end.y
        
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        
        err = dx - dy
        
        while True:
            positions.append(GridPosition(x0, y0))
            
            if x0 == x1 and y0 == y1:
                break
            
            e2 = 2 * err
            
            if e2 > -dy:
                err -= dy
                x0 += sx
            
            if e2 < dx:
                err += dx
                y0 += sy
        
        return positions
    
    def highlight_tiles(self, session_id: str, positions: List[GridPosition], 
                       highlight_type: str):
        """Highlight tiles for visual feedback"""
        for pos in positions:
            tile = self.get_tile(session_id, pos)
            if tile:
                tile.highlight = highlight_type
    
    def clear_highlights(self, session_id: str):
        """Clear all tile highlights"""
        if session_id not in self.battlefields:
            return
        
        for tile in self.battlefields[session_id].values():
            tile.highlight = None
    
    def apply_area_effect(self, session_id: str, center: GridPosition, 
                         radius: int, effect: str, pattern: str = "circle"):
        """Apply area effect to tiles"""
        if pattern == "circle":
            affected_tiles = self.get_tiles_in_range(center, radius, "euclidean")
        elif pattern == "square":
            affected_tiles = self.get_tiles_in_range(center, radius, "chebyshev")
        else:  # line or custom patterns
            affected_tiles = [center]
        
        for pos in affected_tiles:
            tile = self.get_tile(session_id, pos)
            if tile and effect not in tile.effects:
                tile.effects.append(effect)
    
    def _invalidate_pathfinding_cache(self, session_id: str):
        """Invalidate pathfinding cache for session"""
        if session_id in self.pathfinding_cache:
            self.pathfinding_cache[session_id].clear()
    
    async def get_teams_with_living_units(self, session_id: str) -> Set[str]:
        """Get teams that have living units on battlefield"""
        teams = set()
        
        if session_id not in self.battlefields:
            return teams
        
        for tile in self.battlefields[session_id].values():
            if tile.occupant:
                # This would need to query the ECS for team information
                # For now, we'll return a placeholder
                teams.add("team_placeholder")
        
        return teams
    
    async def check_objective_capture(self, session_id: str) -> bool:
        """Check if objectives are captured"""
        # Placeholder for objective capture logic
        return False
    
    async def get_winning_team(self, session_id: str) -> Optional[str]:
        """Get the winning team"""
        teams = await self.get_teams_with_living_units(session_id)
        return list(teams)[0] if len(teams) == 1 else None
    
    async def get_state(self, session_id: str) -> Dict[str, Any]:
        """Get battlefield state"""
        if session_id not in self.battlefields:
            return {}
        
        battlefield = self.battlefields[session_id]
        tiles_data = []
        
        for tile in battlefield.values():
            tiles_data.append({
                "position": {"x": tile.position.x, "y": tile.position.y},
                "terrain_type": tile.terrain_type,
                "status": tile.status,
                "occupant": str(tile.occupant) if tile.occupant else None,
                "height": tile.height,
                "highlight": tile.highlight,
                "effects": tile.effects
            })
        
        return {
            "size": {"width": self.width, "height": self.height},
            "tiles": tiles_data
        }
    
    async def update(self, session_id: str):
        """Update battlefield state"""
        # Clear temporary effects and highlights if needed
        pass
    
    async def cleanup_session(self, session_id: str):
        """Clean up session data"""
        if session_id in self.battlefields:
            del self.battlefields[session_id]
        
        if session_id in self.pathfinding_cache:
            del self.pathfinding_cache[session_id]
        
        logger.info("Battlefield session cleaned up", session_id=session_id)
    
    def get_pathfinding_stats(self) -> Dict[str, Any]:
        """Get pathfinding performance statistics"""
        hit_rate = (self.cache_hits / self.pathfinding_calls 
                   if self.pathfinding_calls > 0 else 0)
        
        return {
            "pathfinding_calls": self.pathfinding_calls,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": hit_rate,
            "active_sessions": len(self.battlefields)
        }

# Alias for backward compatibility
Battlefield = BattlefieldManager