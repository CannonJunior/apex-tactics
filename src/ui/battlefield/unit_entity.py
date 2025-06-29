from ursina import *
from core.models.unit_types import UnitType
from core.assets.unit_data_manager import get_unit_data_manager

class UnitEntity(Entity):
    def __init__(self, unit):
        # Get visual properties from centralized data manager
        data_manager = get_unit_data_manager()
        visual_props = data_manager.get_unit_visual_properties(unit.type)
        
        super().__init__(
            parent=scene,
            model=visual_props['model'],
            color=visual_props['color'],
            scale=tuple(visual_props['scale']),
            position=(unit.x, 1.0, unit.y)
        )
        self.unit = unit
        self.original_color = visual_props['color']
        
    def highlight_selected(self):
        self.color = color.white
        
    def unhighlight(self):
        self.color = self.original_color