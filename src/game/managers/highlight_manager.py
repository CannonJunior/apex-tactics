"""
Highlight Manager

Manages visual tile highlighting and unit highlighting extracted from monolithic controller.
Handles movement range, attack range, magic range, and effect area highlighting.

Features:
- Movement range highlighting (green tiles)
- Attack range highlighting (red tiles)  
- Magic range highlighting (blue tiles)
- Effect area highlighting (yellow tiles)
- Path highlighting for movement planning
- Unit selection highlighting
"""

from typing import List, Dict, Optional, Tuple, Any
from enum import Enum

try:
    from ursina import Entity, color, destroy
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False

from core.models.unit import Unit
from game.interfaces.game_interfaces import IHighlightManager, HighlightType


class HighlightStyle:
    """Visual styling for different highlight types."""
    
    MOVEMENT = {"color": color.green, "alpha": 0.6, "scale": (0.9, 0.2, 0.9)}
    ATTACK = {"color": color.red, "alpha": 0.6, "scale": (0.9, 0.2, 0.9)}
    MAGIC = {"color": color.blue, "alpha": 0.6, "scale": (0.9, 0.2, 0.9)}
    TALENT = {"color": color.magenta, "alpha": 0.6, "scale": (0.9, 0.2, 0.9)}
    PATH = {"color": color.yellow, "alpha": 0.8, "scale": (0.8, 0.3, 0.8)}
    SELECTION = {"color": color.white, "alpha": 0.8, "scale": (0.95, 0.25, 0.95)}
    EFFECT_AREA = {"color": color.orange, "alpha": 0.5, "scale": (0.85, 0.15, 0.85)}


class HighlightManager(IHighlightManager):
    """
    Manages visual highlighting for tactical gameplay.
    
    Extracted from monolithic TacticalRPG controller to provide
    clean separation of visual highlighting concerns.
    """
    
    def __init__(self, grid_width: int = 10, grid_height: int = 8):
        """Initialize highlight manager."""
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for HighlightManager")
        
        self.grid_width = grid_width
        self.grid_height = grid_height
        
        # Highlight entity tracking
        self.highlight_entities: Dict[HighlightType, List[Entity]] = {
            HighlightType.MOVEMENT: [],
            HighlightType.ATTACK: [],
            HighlightType.MAGIC: [],
            HighlightType.TALENT: [],
            HighlightType.PATH: [],
            HighlightType.SELECTION: [],
            HighlightType.EFFECT_AREA: []
        }
        
        # Unit highlighting tracking
        self.highlighted_units: List[Unit] = []
        
        print("✅ HighlightManager initialized")
    
    def highlight_tiles(self, tiles: List[Tuple[int, int]], highlight_type: HighlightType):
        """
        Highlight specified tiles with the given type.
        
        Args:
            tiles: List of (x, y) coordinates to highlight
            highlight_type: Type of highlighting to apply
        """
        # Clear existing highlights of this type
        self.clear_highlights(highlight_type)
        
        # Get style for this highlight type
        style = self._get_highlight_style(highlight_type)
        
        # Create highlight entities
        for x, y in tiles:
            if self._is_valid_position(x, y):
                highlight_entity = self._create_highlight_entity(x, y, style)
                self.highlight_entities[highlight_type].append(highlight_entity)
        
        print(f"🎨 Highlighted {len(tiles)} tiles as {highlight_type.value}")
    
    def highlight_movement_range(self, unit: Unit):
        """Highlight movement range for a unit."""
        if not unit:
            return
        
        movement_tiles = []
        current_x, current_y = unit.x, unit.y
        
        # Calculate movement range using Manhattan distance
        for x in range(self.grid_width):
            for y in range(self.grid_height):
                distance = abs(x - current_x) + abs(y - current_y)
                if distance <= unit.current_move_points and distance > 0:
                    movement_tiles.append((x, y))
        
        # Add current position with different styling
        if movement_tiles:
            # Highlight movement range
            self.highlight_tiles(movement_tiles, HighlightType.MOVEMENT)
            
            # Highlight current position as selection
            self.highlight_tiles([(current_x, current_y)], HighlightType.SELECTION)
        
        print(f"🟢 Movement range highlighted: {len(movement_tiles)} tiles")
    
    def highlight_attack_range(self, unit: Unit):
        """Highlight attack range for a unit."""
        if not unit:
            return
        
        attack_tiles = []
        current_x, current_y = unit.x, unit.y
        
        # Calculate attack range using Manhattan distance
        for x in range(self.grid_width):
            for y in range(self.grid_height):
                distance = abs(x - current_x) + abs(y - current_y)
                if distance <= unit.attack_range and distance > 0:
                    attack_tiles.append((x, y))
        
        self.highlight_tiles(attack_tiles, HighlightType.ATTACK)
        print(f"🔴 Attack range highlighted: {len(attack_tiles)} tiles")
    
    def highlight_magic_range(self, unit: Unit):
        """Highlight magic range for a unit."""
        if not unit:
            return
        
        magic_tiles = []
        current_x, current_y = unit.x, unit.y
        
        # Calculate magic range using Manhattan distance
        for x in range(self.grid_width):
            for y in range(self.grid_height):
                distance = abs(x - current_x) + abs(y - current_y)
                if distance <= unit.magic_range and distance > 0:
                    magic_tiles.append((x, y))
        
        self.highlight_tiles(magic_tiles, HighlightType.MAGIC)
        print(f"🔵 Magic range highlighted: {len(magic_tiles)} tiles")
    
    def highlight_talent_range(self, unit: Unit, talent_range: int):
        """Highlight talent range for a unit."""
        if not unit:
            return
        
        talent_tiles = []
        current_x, current_y = unit.x, unit.y
        
        # Calculate talent range using Manhattan distance
        for x in range(self.grid_width):
            for y in range(self.grid_height):
                distance = abs(x - current_x) + abs(y - current_y)
                if distance <= talent_range and distance > 0:
                    talent_tiles.append((x, y))
        
        self.highlight_tiles(talent_tiles, HighlightType.TALENT)
        print(f"🟣 Talent range highlighted: {len(talent_tiles)} tiles")
    
    def highlight_effect_area(self, center_x: int, center_y: int, effect_radius: int):
        """Highlight effect area around a target position."""
        effect_tiles = []
        
        # Calculate effect area using Manhattan distance
        for x in range(self.grid_width):
            for y in range(self.grid_height):
                distance = abs(x - center_x) + abs(y - center_y)
                if distance <= effect_radius:
                    effect_tiles.append((x, y))
        
        self.highlight_tiles(effect_tiles, HighlightType.EFFECT_AREA)
        print(f"🟠 Effect area highlighted: {len(effect_tiles)} tiles")
    
    def highlight_path(self, path: List[Tuple[int, int]]):
        """Highlight a movement path."""
        if not path:
            return
        
        self.highlight_tiles(path, HighlightType.PATH)
        print(f"🟡 Path highlighted: {len(path)} tiles")
    
    def highlight_unit(self, unit: Unit, highlight_type: HighlightType):
        """Highlight a specific unit."""
        if not unit:
            return
        
        # Find unit's visual entity and highlight it
        # This is a placeholder - will be enhanced when UnitEntity highlighting is integrated
        self.highlighted_units.append(unit)
        print(f"⭐ Unit highlighted: {unit.name}")
    
    def clear_highlights(self, highlight_type: Optional[HighlightType] = None):
        """
        Clear highlights of specified type, or all if None.
        
        Args:
            highlight_type: Type to clear, or None for all types
        """
        if highlight_type is None:
            # Clear all highlight types
            for h_type in HighlightType:
                self._clear_highlight_type(h_type)
            self.highlighted_units.clear()
            print("🧹 All highlights cleared")
        else:
            # Clear specific highlight type
            self._clear_highlight_type(highlight_type)
            print(f"🧹 {highlight_type.value} highlights cleared")
    
    def _clear_highlight_type(self, highlight_type: HighlightType):
        """Clear highlights of a specific type."""
        entities = self.highlight_entities.get(highlight_type, [])
        for entity in entities:
            try:
                destroy(entity)
            except:
                pass  # Entity may already be destroyed
        
        self.highlight_entities[highlight_type] = []
    
    def _create_highlight_entity(self, x: int, y: int, style: Dict[str, Any]) -> Entity:
        """Create a highlight entity at the specified position."""
        return Entity(
            model='cube',
            color=style["color"],
            scale=style["scale"],
            position=(x + 0.5, 0.01, y + 0.5),  # Slightly above ground
            alpha=style["alpha"]
        )
    
    def _get_highlight_style(self, highlight_type: HighlightType) -> Dict[str, Any]:
        """Get visual style for highlight type."""
        style_map = {
            HighlightType.MOVEMENT: HighlightStyle.MOVEMENT,
            HighlightType.ATTACK: HighlightStyle.ATTACK,
            HighlightType.MAGIC: HighlightStyle.MAGIC,
            HighlightType.TALENT: HighlightStyle.TALENT,
            HighlightType.PATH: HighlightStyle.PATH,
            HighlightType.SELECTION: HighlightStyle.SELECTION,
            HighlightType.EFFECT_AREA: HighlightStyle.EFFECT_AREA
        }
        
        return style_map.get(highlight_type, HighlightStyle.SELECTION)
    
    def _is_valid_position(self, x: int, y: int) -> bool:
        """Check if position is within grid bounds."""
        return 0 <= x < self.grid_width and 0 <= y < self.grid_height
    
    def get_highlight_summary(self) -> Dict[str, Any]:
        """Get summary of current highlights."""
        summary = {}
        for h_type in HighlightType:
            count = len(self.highlight_entities.get(h_type, []))
            if count > 0:
                summary[h_type.value] = count
        
        summary["highlighted_units"] = len(self.highlighted_units)
        return summary
    
    def update_grid_size(self, width: int, height: int):
        """Update grid dimensions and clear existing highlights."""
        self.grid_width = width
        self.grid_height = height
        self.clear_highlights()
        print(f"📐 Grid size updated: {width}x{height}")
    
    def shutdown(self):
        """Clean shutdown of highlight manager."""
        self.clear_highlights()
        print("✅ HighlightManager shutdown complete")