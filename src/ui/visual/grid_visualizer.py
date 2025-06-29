"""
Grid Visualization System

Real-time tile highlighting and tactical overlay system for battlefield visualization.
"""

from typing import Dict, List, Set, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass
import time

from core.ecs.entity import Entity
from core.math.vector import Vector3, Vector2Int
from core.math.grid import TacticalGrid
from core.math.pathfinding import AStarPathfinder


class HighlightType(Enum):
    """Types of tile highlights for different tactical information"""
    MOVEMENT = "movement"
    MOVEMENT_PATH = "movement_path"
    ATTACK_RANGE = "attack_range"
    EFFECT_AREA = "effect_area"
    DANGER_ZONE = "danger_zone"
    HEAL_AREA = "heal_area"
    SELECTION = "selection"
    INVALID = "invalid"


@dataclass
class HighlightStyle:
    """Visual style configuration for tile highlights"""
    color: Tuple[float, float, float, float]  # RGBA
    intensity: float = 1.0
    pulse_speed: float = 0.0  # 0 = no pulse
    border_width: float = 0.1
    z_offset: float = 0.01


class GridVisualizer:
    """
    Real-time grid visualization system for tactical overlays.
    
    Provides immediate visual feedback for movement, attack ranges, 
    effect areas, and other tactical information through color-coded tiles.
    """
    
    def __init__(self, grid_system: TacticalGrid, pathfinding: AStarPathfinder):
        self.grid_system = grid_system
        self.pathfinding = pathfinding
        
        # Visual style configuration
        self.highlight_styles = self._create_default_styles()
        
        # Active highlights tracking
        self.active_highlights: Dict[Vector2Int, Set[HighlightType]] = {}
        self.highlight_entities: Dict[Tuple[Vector2Int, HighlightType], Any] = {}
        
        # Animation state
        self.animation_time = 0.0
        self.pulse_animations: Dict[HighlightType, float] = {}
        
        # Performance optimization
        self.dirty_tiles: Set[Vector2Int] = set()
        self.last_update_time = 0.0
        self.update_frequency = 0.016  # 60 FPS
        
        # Selection state
        self.selected_unit: Optional[Entity] = None
        self.hovered_tile: Optional[Vector2Int] = None
        
    def _create_default_styles(self) -> Dict[HighlightType, HighlightStyle]:
        """Create default visual styles for different highlight types"""
        return {
            HighlightType.MOVEMENT: HighlightStyle(
                color=(0.0, 1.0, 0.0, 0.6),  # Green
                intensity=0.8,
                pulse_speed=0.0
            ),
            HighlightType.MOVEMENT_PATH: HighlightStyle(
                color=(0.0, 0.7, 1.0, 0.8),  # Blue
                intensity=1.0,
                pulse_speed=2.0
            ),
            HighlightType.ATTACK_RANGE: HighlightStyle(
                color=(1.0, 0.0, 0.0, 0.7),  # Red
                intensity=0.9,
                pulse_speed=0.5
            ),
            HighlightType.EFFECT_AREA: HighlightStyle(
                color=(1.0, 1.0, 0.0, 0.6),  # Yellow
                intensity=0.8,
                pulse_speed=1.0
            ),
            HighlightType.DANGER_ZONE: HighlightStyle(
                color=(1.0, 0.5, 0.0, 0.8),  # Orange
                intensity=1.0,
                pulse_speed=3.0
            ),
            HighlightType.HEAL_AREA: HighlightStyle(
                color=(0.0, 1.0, 0.8, 0.6),  # Cyan
                intensity=0.7,
                pulse_speed=1.5
            ),
            HighlightType.SELECTION: HighlightStyle(
                color=(1.0, 1.0, 1.0, 0.9),  # White
                intensity=1.0,
                pulse_speed=2.5,
                border_width=0.2
            ),
            HighlightType.INVALID: HighlightStyle(
                color=(0.8, 0.0, 0.8, 0.5),  # Purple
                intensity=0.5,
                pulse_speed=0.0
            )
        }
    
    def update(self, delta_time: float):
        """Update visual animations and effects"""
        current_time = time.time()
        
        # Throttle updates for performance
        if current_time - self.last_update_time < self.update_frequency:
            return
        
        self.animation_time += delta_time
        self.last_update_time = current_time
        
        # Update pulse animations
        for highlight_type, style in self.highlight_styles.items():
            if style.pulse_speed > 0:
                self.pulse_animations[highlight_type] = (
                    0.5 + 0.5 * abs(1.0 - ((self.animation_time * style.pulse_speed) % 2.0))
                )
        
        # Update dirty tiles
        if self.dirty_tiles:
            self._refresh_dirty_tiles()
    
    def set_selected_unit(self, unit: Optional[Entity]):
        """Set the currently selected unit and update tactical overlays"""
        if self.selected_unit == unit:
            return
        
        # Clear previous selection
        if self.selected_unit:
            self.clear_all_highlights()
        
        self.selected_unit = unit
        
        if unit:
            self._update_tactical_overlays(unit)
    
    def set_hovered_tile(self, tile_pos: Optional[Vector2Int]):
        """Set the currently hovered tile"""
        if self.hovered_tile == tile_pos:
            return
        
        # Clear previous hover highlight
        if self.hovered_tile:
            self.remove_tile_highlight(self.hovered_tile, HighlightType.SELECTION)
        
        self.hovered_tile = tile_pos
        
        # Add new hover highlight
        if tile_pos and self.grid_system.is_valid_position(tile_pos):
            self.add_tile_highlight(tile_pos, HighlightType.SELECTION)
    
    def _update_tactical_overlays(self, unit: Entity):
        """Update all tactical overlays for the selected unit"""
        from components.movement.movement import MovementComponent
        from components.combat.attack import AttackComponent
        
        unit_transform = unit.get_component('Transform')
        if not unit_transform:
            return
        
        unit_pos = self.grid_system.world_to_grid(unit_transform.position)
        
        # Show movement options
        movement_comp = unit.get_component(MovementComponent)
        if movement_comp:
            movement_tiles = self._get_movement_tiles(unit, unit_pos)
            self.highlight_tiles(movement_tiles, HighlightType.MOVEMENT)
        
        # Show attack ranges
        attack_comp = unit.get_component(AttackComponent)
        if attack_comp:
            attack_tiles = self._get_attack_tiles(unit, unit_pos)
            self.highlight_tiles(attack_tiles, HighlightType.ATTACK_RANGE)
        
        # Show danger zones (enemy attack ranges)
        danger_tiles = self._get_danger_tiles(unit, unit_pos)
        self.highlight_tiles(danger_tiles, HighlightType.DANGER_ZONE)
    
    def _get_movement_tiles(self, unit: Entity, unit_pos: Vector2Int) -> Set[Vector2Int]:
        """Get tiles reachable by movement"""
        from components.movement.movement import MovementComponent
        
        movement_comp = unit.get_component(MovementComponent)
        if not movement_comp:
            return set()
        
        movement_range = movement_comp.movement_range
        reachable_tiles = set()
        
        # Use optimized flood-fill algorithm instead of individual pathfinding calls
        # This reduces O(n²) pathfinding calls to O(n) grid traversal
        from collections import deque
        
        visited = {unit_pos: 0.0}  # position -> movement cost to reach
        queue = deque([(unit_pos, 0.0)])  # (position, cost_so_far)
        
        while queue:
            current_pos, current_cost = queue.popleft()
            
            # Add this tile as reachable (except starting position)
            if current_pos != unit_pos:
                reachable_tiles.add(current_pos)
            
            # Explore neighbors if we haven't exhausted movement
            if current_cost < movement_range:
                neighbors = self.grid_system.get_neighbors(current_pos, include_diagonals=True)
                
                for neighbor_pos in neighbors:
                    if not self.grid_system.is_valid_position(neighbor_pos):
                        continue
                    
                    # Calculate movement cost to this neighbor
                    move_cost = self.grid_system.get_movement_cost(current_pos, neighbor_pos)
                    new_cost = current_cost + move_cost
                    
                    # Skip if movement cost is infinite (blocked tile)
                    if move_cost == float('inf'):
                        continue
                    
                    # Skip if this neighbor is too expensive to reach
                    if new_cost > movement_range:
                        continue
                    
                    # Skip if we've already found a better path to this neighbor
                    if neighbor_pos in visited and visited[neighbor_pos] <= new_cost:
                        continue
                    
                    # This is a better or new path to this neighbor
                    visited[neighbor_pos] = new_cost
                    queue.append((neighbor_pos, new_cost))
        
        return reachable_tiles
    
    def _get_attack_tiles(self, unit: Entity, unit_pos: Vector2Int) -> Set[Vector2Int]:
        """Get tiles within attack range"""
        from components.combat.attack import AttackComponent
        
        attack_comp = unit.get_component(AttackComponent)
        if not attack_comp:
            return set()
        
        attack_range = attack_comp.attack_range
        attack_tiles = set()
        
        # Calculate tiles within attack range
        for x in range(unit_pos.x - attack_range, unit_pos.x + attack_range + 1):
            for y in range(unit_pos.y - attack_range, unit_pos.y + attack_range + 1):
                target_pos = Vector2Int(x, y)
                
                if not self.grid_system.is_valid_position(target_pos):
                    continue
                
                distance = abs(target_pos.x - unit_pos.x) + abs(target_pos.y - unit_pos.y)
                if distance <= attack_range and distance > 0:
                    attack_tiles.add(target_pos)
        
        return attack_tiles
    
    def _get_danger_tiles(self, unit: Entity, unit_pos: Vector2Int) -> Set[Vector2Int]:
        """Get tiles that are under threat from enemies"""
        # This would need access to enemy units from the world/battle manager
        # For now, return empty set as placeholder
        return set()
    
    def highlight_tiles(self, tiles: Set[Vector2Int], highlight_type: HighlightType):
        """Add highlight to multiple tiles"""
        for tile_pos in tiles:
            self.add_tile_highlight(tile_pos, highlight_type)
    
    def add_tile_highlight(self, tile_pos: Vector2Int, highlight_type: HighlightType):
        """Add a highlight to a specific tile"""
        if not self.grid_system.is_valid_position(tile_pos):
            return
        
        # Add to active highlights
        if tile_pos not in self.active_highlights:
            self.active_highlights[tile_pos] = set()
        
        if highlight_type not in self.active_highlights[tile_pos]:
            self.active_highlights[tile_pos].add(highlight_type)
            self.dirty_tiles.add(tile_pos)
    
    def remove_tile_highlight(self, tile_pos: Vector2Int, highlight_type: HighlightType):
        """Remove a specific highlight from a tile"""
        if tile_pos in self.active_highlights:
            self.active_highlights[tile_pos].discard(highlight_type)
            
            if not self.active_highlights[tile_pos]:
                del self.active_highlights[tile_pos]
            
            self.dirty_tiles.add(tile_pos)
    
    def clear_highlights_of_type(self, highlight_type: HighlightType):
        """Clear all highlights of a specific type"""
        tiles_to_update = set()
        
        for tile_pos, highlights in list(self.active_highlights.items()):
            if highlight_type in highlights:
                highlights.discard(highlight_type)
                tiles_to_update.add(tile_pos)
                
                if not highlights:
                    del self.active_highlights[tile_pos]
        
        self.dirty_tiles.update(tiles_to_update)
    
    def clear_all_highlights(self):
        """Clear all tile highlights"""
        self.dirty_tiles.update(self.active_highlights.keys())
        self.active_highlights.clear()
    
    def show_movement_path(self, path: List[Vector2Int]):
        """Highlight a specific movement path"""
        self.clear_highlights_of_type(HighlightType.MOVEMENT_PATH)
        
        for tile_pos in path:
            self.add_tile_highlight(tile_pos, HighlightType.MOVEMENT_PATH)
    
    def show_effect_area(self, center: Vector2Int, radius: int, effect_type: HighlightType = HighlightType.EFFECT_AREA):
        """Show area effect highlight"""
        effect_tiles = set()
        
        for x in range(center.x - radius, center.x + radius + 1):
            for y in range(center.y - radius, center.y + radius + 1):
                tile_pos = Vector2Int(x, y)
                
                if not self.grid_system.is_valid_position(tile_pos):
                    continue
                
                distance = abs(tile_pos.x - center.x) + abs(tile_pos.y - center.y)
                if distance <= radius:
                    effect_tiles.add(tile_pos)
        
        self.highlight_tiles(effect_tiles, effect_type)
    
    def _refresh_dirty_tiles(self):
        """Update visual representation of dirty tiles"""
        # This method would interface with the actual rendering system
        # For now, we'll just clear the dirty tiles set
        self.dirty_tiles.clear()
    
    def get_highlighted_tiles(self, highlight_type: Optional[HighlightType] = None) -> Set[Vector2Int]:
        """Get all tiles with specific highlight type or all highlighted tiles"""
        if highlight_type is None:
            return set(self.active_highlights.keys())
        
        highlighted_tiles = set()
        for tile_pos, highlights in self.active_highlights.items():
            if highlight_type in highlights:
                highlighted_tiles.add(tile_pos)
        
        return highlighted_tiles
    
    def get_tile_highlights(self, tile_pos: Vector2Int) -> Set[HighlightType]:
        """Get all highlight types for a specific tile"""
        return self.active_highlights.get(tile_pos, set()).copy()
    
    def is_tile_highlighted(self, tile_pos: Vector2Int, highlight_type: HighlightType) -> bool:
        """Check if a tile has a specific highlight"""
        return (tile_pos in self.active_highlights and 
                highlight_type in self.active_highlights[tile_pos])
    
    def get_visual_data_for_tile(self, tile_pos: Vector2Int) -> Optional[Dict[str, Any]]:
        """Get visual data for rendering a highlighted tile"""
        if tile_pos not in self.active_highlights:
            return None
        
        highlights = self.active_highlights[tile_pos]
        
        # Use highest priority highlight for visual
        priority_order = [
            HighlightType.SELECTION,
            HighlightType.MOVEMENT_PATH,
            HighlightType.DANGER_ZONE,
            HighlightType.ATTACK_RANGE,
            HighlightType.EFFECT_AREA,
            HighlightType.HEAL_AREA,
            HighlightType.MOVEMENT,
            HighlightType.INVALID
        ]
        
        primary_highlight = None
        for highlight_type in priority_order:
            if highlight_type in highlights:
                primary_highlight = highlight_type
                break
        
        if not primary_highlight:
            return None
        
        style = self.highlight_styles[primary_highlight]
        world_pos = self.grid_system.grid_to_world(tile_pos)
        
        # Apply pulse animation if configured
        intensity = style.intensity
        if style.pulse_speed > 0 and primary_highlight in self.pulse_animations:
            intensity *= self.pulse_animations[primary_highlight]
        
        return {
            'position': world_pos,
            'color': style.color,
            'intensity': intensity,
            'border_width': style.border_width,
            'z_offset': style.z_offset,
            'highlight_types': list(highlights)
        }
    
    def get_all_visual_data(self) -> List[Dict[str, Any]]:
        """Get visual data for all highlighted tiles"""
        visual_data = []
        
        for tile_pos in self.active_highlights:
            tile_data = self.get_visual_data_for_tile(tile_pos)
            if tile_data:
                visual_data.append(tile_data)
        
        return visual_data
    
    def set_highlight_style(self, highlight_type: HighlightType, style: HighlightStyle):
        """Customize the visual style for a highlight type"""
        self.highlight_styles[highlight_type] = style
        
        # Mark all tiles with this highlight type as dirty
        for tile_pos, highlights in self.active_highlights.items():
            if highlight_type in highlights:
                self.dirty_tiles.add(tile_pos)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for monitoring"""
        return {
            'active_highlights': len(self.active_highlights),
            'dirty_tiles': len(self.dirty_tiles),
            'total_highlight_instances': sum(len(highlights) for highlights in self.active_highlights.values()),
            'animation_time': self.animation_time,
            'last_update_time': self.last_update_time
        }