"""
Tile Highlighter - Ursina Integration

Ursina-specific implementation for rendering tile highlights and visual effects.
"""

from typing import Dict, List, Optional, Any, Tuple
import time

try:
    from ursina import Entity, color, scene, destroy, Mesh, Vec3
    from ursina.shaders import lit_with_shadows_shader
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False

from core.math.vector import Vector2Int, Vector3
from .grid_visualizer import GridVisualizer, HighlightType


class TileHighlighter:
    """
    Ursina-based tile highlighting renderer.
    
    Creates and manages visual tile highlight entities in the Ursina scene.
    """
    
    def __init__(self, grid_visualizer: GridVisualizer, tile_size: float = 1.0):
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for TileHighlighter")
        
        self.grid_visualizer = grid_visualizer
        self.tile_size = tile_size
        
        # Visual entities tracking
        self.highlight_entities: Dict[Vector2Int, Entity] = {}
        self.effect_entities: List[Entity] = []
        
        # Visual configuration
        self.highlight_height = 0.02  # Height above ground
        self.border_height = 0.05     # Height for border highlights
        
        # Animation state
        self.animation_time = 0.0
        
        # Create highlight mesh templates
        self._create_highlight_meshes()
    
    def _create_highlight_meshes(self):
        """Create reusable mesh templates for different highlight types"""
        # Basic tile highlight mesh (slightly smaller than full tile)
        self.tile_mesh = self._create_tile_mesh(self.tile_size * 0.9)
        
        # Border highlight mesh (just the edges)
        self.border_mesh = self._create_border_mesh(self.tile_size)
    
    def _create_tile_mesh(self, size: float) -> Mesh:
        """Create a flat square mesh for tile highlighting"""
        half_size = size / 2
        
        # Simple quad mesh
        vertices = [
            (-half_size, 0, -half_size),
            (half_size, 0, -half_size), 
            (half_size, 0, half_size),
            (-half_size, 0, half_size)
        ]
        
        triangles = [
            (0, 1, 2),
            (0, 2, 3)
        ]
        
        uvs = [
            (0, 0),
            (1, 0),
            (1, 1),
            (0, 1)
        ]
        
        mesh = Mesh(vertices=vertices, triangles=triangles, uvs=uvs)
        return mesh
    
    def _create_border_mesh(self, size: float) -> Mesh:
        """Create a border mesh for selection highlights"""
        half_size = size / 2
        border_width = 0.1
        
        # Create border as separate quads
        vertices = []
        triangles = []
        uvs = []
        
        # Top border
        vertices.extend([
            (-half_size, 0, half_size),
            (half_size, 0, half_size),
            (half_size, 0, half_size - border_width),
            (-half_size, 0, half_size - border_width)
        ])
        
        # Bottom border
        vertices.extend([
            (-half_size, 0, -half_size + border_width),
            (half_size, 0, -half_size + border_width),
            (half_size, 0, -half_size),
            (-half_size, 0, -half_size)
        ])
        
        # Left border
        vertices.extend([
            (-half_size, 0, -half_size + border_width),
            (-half_size + border_width, 0, -half_size + border_width),
            (-half_size + border_width, 0, half_size - border_width),
            (-half_size, 0, half_size - border_width)
        ])
        
        # Right border
        vertices.extend([
            (half_size - border_width, 0, -half_size + border_width),
            (half_size, 0, -half_size + border_width),
            (half_size, 0, half_size - border_width),
            (half_size - border_width, 0, half_size - border_width)
        ])
        
        # Create triangles for each border segment
        for i in range(4):  # 4 border segments
            base_idx = i * 4
            triangles.extend([
                (base_idx, base_idx + 1, base_idx + 2),
                (base_idx, base_idx + 2, base_idx + 3)
            ])
            
            uvs.extend([
                (0, 0), (1, 0), (1, 1), (0, 1)
            ])
        
        mesh = Mesh(vertices=vertices, triangles=triangles, uvs=uvs)
        return mesh
    
    def update(self, delta_time: float):
        """Update visual animations and sync with grid visualizer"""
        self.animation_time += delta_time
        
        # Update the grid visualizer
        self.grid_visualizer.update(delta_time)
        
        # Sync visual entities with grid visualizer state
        self._sync_visual_entities()
        
        # Update animations
        self._update_animations()
    
    def _sync_visual_entities(self):
        """Synchronize Ursina entities with grid visualizer highlights"""
        current_highlights = set(self.grid_visualizer.active_highlights.keys())
        existing_entities = set(self.highlight_entities.keys())
        
        # Remove entities for tiles that are no longer highlighted
        tiles_to_remove = existing_entities - current_highlights
        for tile_pos in tiles_to_remove:
            self._remove_highlight_entity(tile_pos)
        
        # Add/update entities for highlighted tiles
        for tile_pos in current_highlights:
            self._update_highlight_entity(tile_pos)
    
    def _update_highlight_entity(self, tile_pos: Vector2Int):
        """Update or create highlight entity for a tile"""
        visual_data = self.grid_visualizer.get_visual_data_for_tile(tile_pos)
        if not visual_data:
            return
        
        # Create entity if it doesn't exist
        if tile_pos not in self.highlight_entities:
            self._create_highlight_entity(tile_pos, visual_data)
        else:
            self._update_existing_entity(tile_pos, visual_data)
    
    def _create_highlight_entity(self, tile_pos: Vector2Int, visual_data: Dict[str, Any]):
        """Create a new highlight entity"""
        world_pos = visual_data['position']
        highlight_types = visual_data['highlight_types']
        
        # Choose appropriate mesh based on highlight types
        if HighlightType.SELECTION in highlight_types:
            mesh = self.border_mesh
            y_offset = self.border_height
        else:
            mesh = self.tile_mesh
            y_offset = self.highlight_height
        
        # Create the entity
        entity = Entity(
            model=mesh,
            position=Vec3(world_pos.x, world_pos.y + y_offset, world_pos.z),
            color=self._convert_color(visual_data['color']),
            shader=lit_with_shadows_shader,
            parent=scene
        )
        
        # Store additional data for animations
        entity.base_intensity = visual_data['intensity']
        entity.highlight_types = highlight_types
        entity.tile_pos = tile_pos
        
        self.highlight_entities[tile_pos] = entity
    
    def _update_existing_entity(self, tile_pos: Vector2Int, visual_data: Dict[str, Any]):
        """Update properties of existing highlight entity"""
        entity = self.highlight_entities[tile_pos]
        
        # Update color and intensity
        entity.color = self._convert_color(visual_data['color'])
        entity.base_intensity = visual_data['intensity']
        entity.highlight_types = visual_data['highlight_types']
        
        # Update position if needed
        world_pos = visual_data['position']
        if HighlightType.SELECTION in visual_data['highlight_types']:
            y_offset = self.border_height
        else:
            y_offset = self.highlight_height
        
        entity.position = Vec3(world_pos.x, world_pos.y + y_offset, world_pos.z)
    
    def _remove_highlight_entity(self, tile_pos: Vector2Int):
        """Remove highlight entity for a tile"""
        if tile_pos in self.highlight_entities:
            entity = self.highlight_entities[tile_pos]
            destroy(entity)
            del self.highlight_entities[tile_pos]
    
    def _update_animations(self):
        """Update animation effects on highlight entities"""
        for tile_pos, entity in self.highlight_entities.items():
            # Get current visual data for animation parameters
            visual_data = self.grid_visualizer.get_visual_data_for_tile(tile_pos)
            if not visual_data:
                continue
            
            # Apply intensity animation (pulsing effect)
            animated_intensity = visual_data['intensity']
            
            # Update entity alpha based on animated intensity
            current_color = entity.color
            new_color = color.Color(
                current_color.r,
                current_color.g, 
                current_color.b,
                animated_intensity
            )
            entity.color = new_color
    
    def _convert_color(self, rgba_tuple: Tuple[float, float, float, float]) -> color.Color:
        """Convert RGBA tuple to Ursina color"""
        r, g, b, a = rgba_tuple
        return color.Color(r, g, b, a)
    
    def clear_all_highlights(self):
        """Clear all highlight entities"""
        for entity in self.highlight_entities.values():
            destroy(entity)
        
        self.highlight_entities.clear()
        self.grid_visualizer.clear_all_highlights()
    
    def set_selected_unit(self, unit):
        """Set selected unit and update highlights"""
        self.grid_visualizer.set_selected_unit(unit)
    
    def set_hovered_tile(self, tile_pos: Optional[Vector2Int]):
        """Set hovered tile and update highlights"""
        self.grid_visualizer.set_hovered_tile(tile_pos)
    
    def show_movement_path(self, path: List[Vector2Int]):
        """Show movement path with highlights"""
        self.grid_visualizer.show_movement_path(path)
    
    def show_effect_area(self, center: Vector2Int, radius: int, 
                        effect_type: HighlightType = HighlightType.EFFECT_AREA):
        """Show area effect with highlights"""
        self.grid_visualizer.show_effect_area(center, radius, effect_type)
    
    def create_floating_effect(self, position: Vector3, effect_type: str, 
                             duration: float = 2.0) -> Entity:
        """Create a floating visual effect at a position"""
        if not URSINA_AVAILABLE:
            return None
        
        # Create floating effect entity
        effect_entity = Entity(
            model='cube',
            scale=0.2,
            position=Vec3(position.x, position.y + 1.0, position.z),
            color=color.yellow,
            parent=scene
        )
        
        # Store effect data
        effect_entity.effect_type = effect_type
        effect_entity.start_time = time.time()
        effect_entity.duration = duration
        effect_entity.start_position = Vec3(position.x, position.y + 1.0, position.z)
        
        self.effect_entities.append(effect_entity)
        return effect_entity
    
    def update_floating_effects(self, delta_time: float):
        """Update floating visual effects"""
        current_time = time.time()
        effects_to_remove = []
        
        for effect in self.effect_entities:
            elapsed = current_time - effect.start_time
            progress = elapsed / effect.duration
            
            if progress >= 1.0:
                effects_to_remove.append(effect)
                continue
            
            # Animate the effect (float upward and fade)
            effect.position = Vec3(
                effect.start_position.x,
                effect.start_position.y + progress * 2.0,
                effect.start_position.z
            )
            
            # Fade out
            alpha = 1.0 - progress
            effect.color = color.Color(
                effect.color.r,
                effect.color.g,
                effect.color.b,
                alpha
            )
        
        # Remove expired effects
        for effect in effects_to_remove:
            destroy(effect)
            self.effect_entities.remove(effect)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance and status statistics"""
        return {
            'active_highlight_entities': len(self.highlight_entities),
            'active_effect_entities': len(self.effect_entities),
            'grid_visualizer_stats': self.grid_visualizer.get_performance_stats()
        }
    
    def cleanup(self):
        """Clean up all visual entities"""
        self.clear_all_highlights()
        
        # Clean up floating effects
        for effect in self.effect_entities:
            destroy(effect)
        self.effect_entities.clear()