"""
Targeted Unit Management Methods

"""

from core.assets.talent_type_config import get_talent_type_config
from ui.core.ui_style_manager import get_ui_style_manager
from ursina import Entity, color, destroy, Button, Text, WindowPanel, camera, Tooltip
from ursina.prefabs.health_bar import HealthBar

def target_add_targeted_unit(self, unit):
    """Add a unit to the targeted units list"""
    if unit not in self.targeted_units:
        self.targeted_units.append(unit)
        self.update_targeted_unit_bars()
    
def target_remove_targeted_unit(self, unit):
    """Remove a unit from the targeted units list"""
    if unit in self.targeted_units:
        self.targeted_units.remove(unit)
        self.update_targeted_unit_bars()
    
def target_clear_targeted_units(self):
    """Clear all targeted units"""
    self.targeted_units.clear()
    self.update_targeted_unit_bars()
    
def target_set_targeted_units(self, units):
    """Set the targeted units list (replaces existing)"""
    self.targeted_units = list(units)
    self.update_targeted_unit_bars()
    
def target_update_targeted_unit_bars(self):
    """Update health and resource bars for all targeted units"""
    # Clear existing targeted unit bars
    self.hide_targeted_unit_bars()
        
    # Create bars for each targeted unit
    if self.targeted_units:
        style_manager = get_ui_style_manager()
            
        for i, unit in enumerate(self.targeted_units):
            # Calculate position for multiple units (stack vertically)
            base_x = 0.4  # Right side of screen
            base_y = 0.45 - (i * 0.1)  # Stack downward
                
            # Create health bar label
            health_label = Text(
                text=f"{unit.name} HP",
                parent=camera.ui,
                position=(base_x - 0.07, base_y),
                scale=0.8,
                color=style_manager.get_bar_label_color(),
                origin=(-0.5, 0.8)
            )
            self.targeted_health_bar_labels.append(health_label)
                
            # Create health bar
            health_bar = HealthBar(
                max_value=unit.max_hp,
                value=unit.hp,
                position=(base_x + 0.05, base_y),
                parent=camera.ui,
                scale=(0.25, 0.025),
                color=style_manager.get_health_bar_bg_color()
            )
                
            # Set health bar color
            if hasattr(health_bar, 'bar'):
                health_bar.bar.color = style_manager.get_health_bar_color()
                
            self.targeted_health_bars.append(health_bar)
                
            # Create resource bar label
            resource_type = unit.primary_resource_type
            resource_value = unit.get_primary_resource_value()
            resource_max = unit.get_primary_resource_max()
            resource_label_text = style_manager.get_resource_bar_label(resource_type)
                
            resource_label = Text(
                text=f"{unit.name} {resource_label_text}",
                parent=camera.ui,
                position=(base_x - 0.07, base_y - 0.03),
                scale=0.8,
                color=style_manager.get_bar_label_color(),
                origin=(-0.5, 0.8)
            )
            self.targeted_resource_bar_labels.append(resource_label)
                
            # Create resource bar
            resource_bar = HealthBar(
                max_value=resource_max,
                value=resource_value,
                position=(base_x + 0.05, base_y - 0.03),
                parent=camera.ui,
                scale=(0.25, 0.025),
                color=style_manager.get_resource_bar_bg_color()
            )
                
            # Set resource bar color
            bar_color = style_manager.get_resource_bar_color(resource_type)
            if hasattr(resource_bar, 'bar'):
                resource_bar.bar.color = bar_color
                
            self.targeted_resource_bars.append(resource_bar)
    
def target_hide_targeted_unit_bars(self):
    """Hide all targeted unit health and resource bars"""
    # Hide and clear health bars
    for bar in self.targeted_health_bars:
        if bar:
            bar.enabled = False
    self.targeted_health_bars.clear()
        
    # Hide and clear health bar labels
    for label in self.targeted_health_bar_labels:
        if label:
            label.enabled = False
    self.targeted_health_bar_labels.clear()
        
    # Hide and clear resource bars
    for bar in self.targeted_resource_bars:
        if bar:
            bar.enabled = False
    self.targeted_resource_bars.clear()
    
    # Hide and clear resource bar labels
    for label in self.targeted_resource_bar_labels:
        if label:
            label.enabled = False
    self.targeted_resource_bar_labels.clear()
    
def target_refresh_targeted_unit_bars(self):
    """Refresh all targeted unit bars to match current HP/resource values"""
    for i, unit in enumerate(self.targeted_units):
        if i < len(self.targeted_health_bars):
            health_bar = self.targeted_health_bars[i]
            if health_bar:
                health_bar.value = unit.hp
            
        if i < len(self.targeted_resource_bars):
            resource_bar = self.targeted_resource_bars[i]
            if resource_bar:
                resource_bar.value = unit.get_primary_resource_value()
    
def target_highlight_magic_range_no_clear(self, unit):
    """Highlight all tiles within the unit's magic range in blue (without clearing existing highlights)."""
    if not unit:
        return
        
    for x in range(self.grid.width):
        for y in range(self.grid.height):
            # Calculate Manhattan distance from unit to tile
            distance = abs(x - unit.x) + abs(y - unit.y)
                
            # Highlight tiles within magic range (excluding unit's own tile)
            if distance <= unit.magic_range and distance > 0:
                # Check if tile is within grid bounds
                if 0 <= x < self.grid.width and 0 <= y < self.grid.height:
                    # Create highlight overlay entity
                    highlight = Entity(
                        model='cube',
                        color=color.blue,
                        scale=(0.9, 0.2, 0.9),
                        position=(x + 0.5, 0, y + 0.5),  # Same height as grid tiles
                        alpha=1.0  # Same transparency as grid
                    )
                    # Store in a list for cleanup
                    if not hasattr(self, 'highlight_entities'):
                        self.highlight_entities = []
                    self.highlight_entities.append(highlight)
    
def target_highlight_talent_range_no_clear(self, unit, talent_type: str, highlight_color):
    """Highlight the talent-specific range around the unit (without clearing existing highlights)."""
    if not unit:
        return
        
    # Get talent-specific range or fall back to type default
    talent_config = get_talent_type_config()
    talent_range = getattr(unit, '_talent_magic_range', talent_config.get_default_range(talent_type))
        
    for x in range(self.grid.width):
        for y in range(self.grid.height):
            # Calculate Manhattan distance from unit to tile
            distance = abs(x - unit.x) + abs(y - unit.y)
                
            # Highlight tiles within talent range (excluding unit's own tile)
            if distance <= talent_range and distance > 0:
                # Check if tile is within grid bounds
                if 0 <= x < self.grid.width and 0 <= y < self.grid.height:
                    # Create highlight overlay entity with type-specific color
                    highlight = Entity(
                        model='cube',
                        color=highlight_color,
                        scale=(0.9, 0.2, 0.9),
                        position=(x + 0.5, 0, y + 0.5),  # Same height as grid tiles
                        alpha=1.0  # Same transparency as standard highlighting
                    )
                    # Store in a list for cleanup
                    if not hasattr(self, 'highlight_entities'):
                        self.highlight_entities = []
                    self.highlight_entities.append(highlight)
