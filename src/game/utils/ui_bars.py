"""
Update Health and Resource bars

"""

from ui.core.ui_style_manager import get_ui_style_manager
from ursina import Entity, color, destroy, Button, Text, WindowPanel, camera, Tooltip
from ursina.prefabs.health_bar import HealthBar

def util_update_health_bar(self, unit):
    """Create or update health bar for the selected unit"""
    if self.health_bar:
        self.health_bar.enabled = False
        self.health_bar = None

    if self.health_bar_label:
        self.health_bar_label.enabled = False
        self.health_bar_label = None

    if unit:
        # Get UI style manager
        style_manager = get_ui_style_manager()

        # Create health bar label
        self.health_bar_label = Text(
            text="HP",
            parent=camera.ui,
            position=(-0.47, 0.43),  # Position to the left of health bar
            scale=1.0,
            color=style_manager.get_bar_label_color(),
            origin=(-0.5, 0)  # Right-align the text
        )

        self.health_bar = HealthBar(
            max_value=unit.max_hp,
            value=unit.hp,
            position=(-0.4, 0.45),
            parent=camera.ui,
            scale=(0.3, 0.03),
            color=style_manager.get_health_bar_bg_color()  # Background color
        )

        # Set the foreground bar color after creation
        if hasattr(self.health_bar, 'bar'):
            self.health_bar.bar.color = style_manager.get_health_bar_color()

def util_hide_health_bar(self):
    """Hide the health bar when no unit is selected"""
    if self.health_bar:
        self.health_bar.enabled = False
        self.health_bar = None

    if self.health_bar_label:
        self.health_bar_label.enabled = False
        self.health_bar_label = None

def util_refresh_health_bar(self):
    """Refresh health bar to match selected unit's current HP"""
    if self.health_bar and self.active_unit:
        self.health_bar.value = self.active_unit.hp

def util_on_unit_hp_changed(self, unit):
    """Called when a unit's HP changes to update health bar if it's the selected unit"""
    if self.active_unit and self.active_unit == unit:
        self.refresh_health_bar()

def util_update_resource_bar(self, unit):
    """Create or update resource bar for the selected unit"""
    if self.resource_bar:
        self.resource_bar.enabled = False
        self.resource_bar = None

    if self.resource_bar_label:
        self.resource_bar_label.enabled = False
        self.resource_bar_label = None

    if unit:
        # Get UI style manager
        style_manager = get_ui_style_manager()

        # Get resource type and values based on unit type
        resource_type = unit.primary_resource_type
        resource_value = unit.get_primary_resource_value()
        resource_max = unit.get_primary_resource_max()

        # Get color and label from style manager
        bar_color = style_manager.get_resource_bar_color(resource_type)
        label_text = style_manager.get_resource_bar_label(resource_type)

        # Create resource bar label
        self.resource_bar_label = Text(
            text=label_text,
            parent=camera.ui,
            position=(-0.47, 0.4),  # Position to the left of resource bar
            scale=1.0,
            color=style_manager.get_bar_label_color(),
            origin=(-0.5, 0)  # Right-align the text
        )

        self.resource_bar = HealthBar(
            max_value=resource_max,
            value=resource_value,
            position=(-0.4, 0.42),  # Position just below health bar
            parent=camera.ui,
            scale=(0.3, 0.03),
            color=style_manager.get_resource_bar_bg_color()  # Background color
        )

        # Set the foreground bar color after creation
        if hasattr(self.resource_bar, 'bar'):
            self.resource_bar.bar.color = bar_color

def util_hide_resource_bar(self):
    """Hide the resource bar when no unit is selected"""
    if self.resource_bar:
        self.resource_bar.enabled = False
        self.resource_bar = None

    if self.resource_bar_label:
        self.resource_bar_label.enabled = False
        self.resource_bar_label = None

def util_refresh_resource_bar(self):
    """Refresh resource bar to match selected unit's current resource value"""
    if self.resource_bar and self.active_unit:
        self.resource_bar.value = self.active_unit.get_primary_resource_value()

def util_on_unit_resource_changed(self, unit):
    """Called when a unit's resource changes to update resource bar if it's the selected unit"""
    if self.active_unit and self.active_unit == unit:
        self.refresh_resource_bar()

def util_update_action_points_bar(self, unit):
    """Create or update action points bar for the selected unit"""
    if self.action_points_bar:
        self.action_points_bar.enabled = False
        self.action_points_bar = None

    if self.action_points_bar_label:
        self.action_points_bar_label.enabled = False
        self.action_points_bar_label = None

    if unit:
        # Get UI style manager
        style_manager = get_ui_style_manager()

        # Create action points bar label
        self.action_points_bar_label = Text(
            text="AP",
            parent=camera.ui,
            position=(-0.47, 0.37),  # Position below resource bar
            scale=1.0,
            color=style_manager.get_bar_label_color(),
            origin=(-0.5, 0)  # Right-align the text
        )

        self.action_points_bar = HealthBar(
            max_value=unit.max_ap if hasattr(unit, 'max_ap') else 10,
            value=unit.ap if hasattr(unit, 'ap') else 10,
            position=(-0.4, 0.39),  # Position below resource bar
            parent=camera.ui,
            scale=(0.3, 0.03),
            color=style_manager.get_action_points_bar_bg_color()  # Background color
        )

        # Set the foreground bar color after creation
        if hasattr(self.action_points_bar, 'bar'):
            self.action_points_bar.bar.color = style_manager.get_action_points_bar_color()

def util_hide_action_points_bar(self):
    """Hide the action points bar when no unit is selected"""
    if self.action_points_bar:
        self.action_points_bar.enabled = False
        self.action_points_bar = None

    if self.action_points_bar_label:
        self.action_points_bar_label.enabled = False
        self.action_points_bar_label = None

def util_refresh_action_points_bar(self):
    """Refresh action points bar to match selected unit's current AP"""
    if self.action_points_bar and self.active_unit:
        ap_value = self.active_unit.ap if hasattr(self.active_unit, 'ap') else 10
        self.action_points_bar.value = ap_value

def util_on_unit_action_points_changed(self, unit):
    """Called when a unit's action points change to update AP bar if it's the selected unit"""
    if self.active_unit and self.active_unit == unit:
        self.refresh_action_points_bar()
