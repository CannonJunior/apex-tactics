"""
Unit Visual Renderer

Handles 3D visual representation of units in the tactical game.
Extracted from apex-tactics.py for better modularity.
"""

from typing import Dict, Any

try:
    from ursina import Entity, color, scene
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False

from core.models.unit_types import UnitType
from core.assets.unit_data_manager import get_unit_data_manager


class UnitEntity(Entity):
    """
    3D visual representation of a unit.
    
    Creates a colored cube entity that represents a unit on the battlefield,
    with highlighting capabilities for selection feedback.
    """
    
    def __init__(self, unit: Any):
        """
        Initialize unit visual entity.
        
        Args:
            unit: Unit object with type, position, and other properties
        """
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for UnitEntity")
        
        # Get visual properties from data manager and master UI config
        data_manager = get_unit_data_manager()
        visual_props = data_manager.get_unit_visual_properties(unit.type)
        
        # Get position offset and unit configuration from master UI config
        from src.core.ui.ui_config_manager import get_ui_config_manager
        ui_config = get_ui_config_manager()
        position_offset = ui_config.get_position('battlefield.units.position_offset')
        unit_scale = ui_config.get_scale('battlefield.units.scale')
        unit_model = ui_config.get('battlefield.units.model', 'cube')
        
        # Use config values, with data manager as override
        final_model = visual_props.get('model', unit_model)
        final_scale = visual_props.get('scale', [unit_scale['x'], unit_scale['y'], unit_scale['z']])
        
        super().__init__(
            parent=scene,
            model=final_model,
            color=visual_props['color'],
            scale=tuple(final_scale),
            position=(unit.x + position_offset['x'], position_offset['y'], unit.y + position_offset['z'])
        )
        
        self.unit = unit
        self.original_color = visual_props['color']
        self.ui_config = ui_config  # Store reference for other methods
    
    def _get_unit_color(self, unit_type: UnitType):
        """
        Get color for unit type.
        
        Args:
            unit_type: UnitType enum value
            
        Returns:
            Color object for the unit type
        """
        data_manager = get_unit_data_manager()
        return data_manager.get_unit_color(unit_type)
    
    def highlight_selected(self):
        """Highlight unit as selected using master UI config."""
        self.color = self.ui_config.get_color('colors.ui_states.selected', '#FFFF00')
    
    def unhighlight(self):
        """Remove selection highlighting."""
        self.color = self.original_color
    
    def update_position(self, x: int, y: int):
        """
        Update unit position using master UI config.
        
        Args:
            x, y: New grid coordinates
        """
        position_offset = self.ui_config.get_position('battlefield.units.position_offset')
        self.position = (x + position_offset['x'], position_offset['y'], y + position_offset['z'])
        if hasattr(self.unit, 'x') and hasattr(self.unit, 'y'):
            self.unit.x, self.unit.y = x, y
    
    def set_health_indicator(self, health_percentage: float):
        """
        Update visual health indicator using master UI config.
        
        Args:
            health_percentage: Health as percentage (0.0 to 1.0)
        """
        # Check if health visual feedback is enabled
        if not self.ui_config.get('battlefield.units.health_visual_feedback.enabled', True):
            return
        
        # Get thresholds from config
        healthy_threshold = self.ui_config.get('battlefield.units.health_visual_feedback.healthy_threshold', 0.7)
        wounded_threshold = self.ui_config.get('battlefield.units.health_visual_feedback.wounded_threshold', 0.3)
        
        if health_percentage > healthy_threshold:
            # Healthy - keep original color
            self.color = self.original_color
        elif health_percentage > wounded_threshold:
            # Wounded - use config color
            self.color = self.ui_config.get_color('battlefield.units.health_visual_feedback.colors.wounded', '#FFA500')
        else:
            # Critical - use config color
            self.color = self.ui_config.get_color('battlefield.units.health_visual_feedback.colors.critical', '#8B0000')
    
    def cleanup(self):
        """Clean up visual entity."""
        if hasattr(self, 'enabled'):
            self.enabled = False