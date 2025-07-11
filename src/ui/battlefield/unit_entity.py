from ursina import *
from core.models.unit_types import UnitType
from core.assets.unit_data_manager import get_unit_data_manager

class UnitEntity(Entity):
    def __init__(self, unit):
        # Load master UI configuration
        from src.core.ui.ui_config_manager import get_ui_config_manager
        ui_config = get_ui_config_manager()
        
        # Get visual properties from centralized data manager
        data_manager = get_unit_data_manager()
        visual_props = data_manager.get_unit_visual_properties(unit.type)
        
        # Get position configuration from master UI config
        entity_config = ui_config.get('ui_battlefield.unit_entity', {})
        position_offset = entity_config.get('position_offset', {'x': 0.5, 'y': 1.0, 'z': 0.5})
        parent_type = entity_config.get('parent', 'scene')
        
        super().__init__(
            parent=scene if parent_type == 'scene' else None,
            model=visual_props['model'],
            color=visual_props['color'],
            scale=tuple(visual_props['scale']),
            position=(unit.x + position_offset['x'], position_offset['y'], unit.y + position_offset['z'])
        )
        self.unit = unit
        self.original_color = visual_props['color']
        
        # Store UI config reference
        self.ui_config = ui_config
        
    def highlight_selected(self):
        # Get highlight color from master UI config
        highlight_color = self.ui_config.get_color('ui_battlefield.unit_entity.highlight_selected_color', '#FFFFFF')
        self.color = highlight_color
        
    def unhighlight(self):
        self.color = self.original_color