"""
Combat Interface

UI for combat actions, turn management, and battle information display.
"""

from typing import Dict, List, Optional, Any
from enum import Enum

try:
    from ursina import Entity, Text, Button, color, camera, scene, destroy
    from ursina import Panel, ProgressBar, Slider
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False

from core.ecs.entity import Entity as GameEntity
from components.stats.attributes import AttributeStats
from game.config.action_costs import ACTION_COSTS


class CombatInterface:
    """
    Combat UI for turn-based tactical battles.
    
    Provides action buttons, unit information, turn order display,
    and battle status information.
    """
    
    def __init__(self):
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for CombatInterface")
        
        # Load master UI configuration
        from src.core.ui.ui_config_manager import get_ui_config_manager
        self.ui_config = get_ui_config_manager()
        
        # Interface state
        self.is_visible = False
        self.selected_unit: Optional[GameEntity] = None
        self.available_actions: List[str] = []
        
        # UI elements
        self.ui_elements: List[Entity] = []
        self.action_buttons: List[Button] = []
        self.unit_info_panel: Optional[Entity] = None
        self.turn_order_panel: Optional[Entity] = None
        
        # Create interface
        self._create_interface()
    
    def _create_interface(self):
        """Create the combat interface elements using master UI config"""
        # Get panel configuration from master UI config
        unit_info_config = self.ui_config.get('ui_interface.combat_interface.unit_info_panel', {})
        turn_order_config = self.ui_config.get('ui_interface.combat_interface.turn_order_panel', {})
        
        # Unit info panel (top left) using master UI config
        panel_model = unit_info_config.get('model', 'cube')
        panel_scale = self.ui_config.get_scale('ui_interface.combat_interface.unit_info_panel.scale')
        panel_color = self.ui_config.get_color_rgba('ui_interface.combat_interface.unit_info_panel.color', (0.1, 0.1, 0.15, 0.9))
        panel_position = self.ui_config.get_position_tuple('ui_interface.combat_interface.unit_info_panel.position')
        parent_type = unit_info_config.get('parent', 'camera.ui')
        
        self.unit_info_panel = Entity(
            model=panel_model,
            scale=panel_scale,
            color=color.Color(*panel_color),
            position=panel_position,
            parent=camera.ui if parent_type == 'camera.ui' else scene,
            visible=False
        )
        
        # Turn order panel (top right) using master UI config
        turn_model = turn_order_config.get('model', 'cube')
        turn_scale = self.ui_config.get_scale('ui_interface.combat_interface.turn_order_panel.scale')
        turn_color = self.ui_config.get_color_rgba('ui_interface.combat_interface.turn_order_panel.color', (0.1, 0.1, 0.15, 0.9))
        turn_position = self.ui_config.get_position_tuple('ui_interface.combat_interface.turn_order_panel.position')
        turn_parent_type = turn_order_config.get('parent', 'camera.ui')
        
        self.turn_order_panel = Entity(
            model=turn_model,
            scale=turn_scale,
            color=color.Color(*turn_color),
            position=turn_position,
            parent=camera.ui if turn_parent_type == 'camera.ui' else scene,
            visible=False
        )
        
        # Action buttons panel (bottom center)
        self._create_action_buttons()
        
        self.ui_elements.extend([self.unit_info_panel, self.turn_order_panel])
    
    def _create_action_buttons(self):
        """Create action buttons for combat using master UI config"""
        # Get button configuration from master UI config
        button_config = self.ui_config.get('ui_interface.combat_interface.action_buttons', {})
        button_y = button_config.get('y_position', -0.4)
        button_spacing = button_config.get('spacing', 0.15)
        button_scale = button_config.get('scale', 0.08)
        button_z_offset = button_config.get('z_offset', 0.01)
        
        # Colors from master UI config
        button_normal_color = self.ui_config.get_color_rgba('ui_interface.combat_interface.action_buttons.colors.normal', (0.3, 0.3, 0.35, 1.0))
        button_text_color = self.ui_config.get_color('ui_interface.combat_interface.action_buttons.colors.text', '#FFFFFF')
        button_parent_type = button_config.get('parent', 'camera.ui')
        
        # Action button configuration from master UI config
        action_list = button_config.get('action_list', ['Move', 'Attack', 'Ability', 'Guard', 'Wait', 'End Turn'])
        
        for i, action in enumerate(action_list):
            x_pos = (i - len(action_list) / 2 + 0.5) * button_spacing
            
            button = Button(
                text=action,
                position=(x_pos, button_y, button_z_offset),
                scale=button_scale,
                color=color.Color(*button_normal_color),
                text_color=button_text_color,
                parent=camera.ui if button_parent_type == 'camera.ui' else scene,
                on_click=lambda a=action: self._on_action_click(a),
                visible=False
            )
            
            self.action_buttons.append(button)
            self.ui_elements.append(button)
    
    def show(self):
        """Show the combat interface"""
        self.is_visible = True
        
        for element in self.ui_elements:
            element.visible = True
        
        for button in self.action_buttons:
            button.visible = True
    
    def hide(self):
        """Hide the combat interface"""
        self.is_visible = False
        
        for element in self.ui_elements:
            element.visible = False
        
        for button in self.action_buttons:
            button.visible = False
    
    def set_selected_unit(self, unit: Optional[GameEntity]):
        """Set the currently selected unit"""
        self.selected_unit = unit
        self._update_unit_info()
        self._update_available_actions()
    
    def _update_unit_info(self):
        """Update the unit information display"""
        # Clear existing info
        for child in self.unit_info_panel.children:
            destroy(child)
        
        if not self.selected_unit:
            return
        
        # Unit name using master UI config
        text_config = self.ui_config.get('ui_interface.combat_interface.unit_info_text', {})
        name_position = text_config.get('name_position', (0, 0.07, 0.01))
        name_scale = text_config.get('name_scale', 1.2)
        name_color = self.ui_config.get_color('ui_interface.combat_interface.unit_info_text.name_color', '#FFFFFF')
        
        unit_name = Text(
            f'Unit {self.selected_unit.id}',
            position=name_position,
            scale=name_scale,
            color=name_color,
            parent=self.unit_info_panel
        )
        
        # Health bar
        attributes = self.selected_unit.get_component(AttributeStats)
        if attributes:
            hp_ratio = attributes.current_hp / attributes.max_hp
            
            # HP text using master UI config
            hp_text_position = text_config.get('hp_text_position', (0, 0.03, 0.01))
            hp_text_scale = text_config.get('hp_text_scale', 0.8)
            hp_text_color = self.ui_config.get_color('ui_interface.combat_interface.unit_info_text.hp_color', '#FFFFFF')
            
            hp_text = Text(
                f'HP: {attributes.current_hp}/{attributes.max_hp}',
                position=hp_text_position,
                scale=hp_text_scale,
                color=hp_text_color,
                parent=self.unit_info_panel
            )
            
            # Health bar configuration from master UI config
            bar_config = self.ui_config.get('ui_interface.combat_interface.health_bar', {})
            bar_model = bar_config.get('model', 'cube')
            bar_width = bar_config.get('width', 0.2)
            bar_height = bar_config.get('height', 0.02)
            bar_bg_position = bar_config.get('bg_position', (0, -0.01, 0.001))
            bar_bg_color = self.ui_config.get_color('ui_interface.combat_interface.health_bar.bg_color', '#2F2F2F')
            
            # Simple health bar representation
            hp_bar_bg = Entity(
                model=bar_model,
                scale=(bar_width, bar_height, 0.001),
                color=bar_bg_color,
                position=bar_bg_position,
                parent=self.unit_info_panel
            )
            
            # Health bar fill colors from master UI config
            hp_colors = self.ui_config.get('ui_interface.combat_interface.health_bar.fill_colors', {})
            hp_low_threshold = bar_config.get('low_threshold', 0.3)
            hp_medium_threshold = bar_config.get('medium_threshold', 0.7)
            hp_low_color = self.ui_config.get_color('ui_interface.combat_interface.health_bar.fill_colors.low', '#FF0000')
            hp_medium_color = self.ui_config.get_color('ui_interface.combat_interface.health_bar.fill_colors.medium', '#FFFF00')
            hp_high_color = self.ui_config.get_color('ui_interface.combat_interface.health_bar.fill_colors.high', '#00FF00')
            
            hp_bar_fill = Entity(
                model=bar_model,
                scale=(bar_width * hp_ratio, bar_height, 0.001),
                color=hp_low_color if hp_ratio < hp_low_threshold else hp_medium_color if hp_ratio < hp_medium_threshold else hp_high_color,
                position=((-bar_width + bar_width * hp_ratio) / 2, -0.01, 0.002),
                parent=self.unit_info_panel
            )
            
            # MP bar if available
            if attributes.max_mp > 0:
                mp_ratio = attributes.current_mp / attributes.max_mp
                
                # MP text using master UI config
                mp_text_position = text_config.get('mp_text_position', (0, -0.05, 0.01))
                mp_text_scale = text_config.get('mp_text_scale', 0.8)
                mp_text_color = self.ui_config.get_color('ui_interface.combat_interface.unit_info_text.mp_color', '#FFFFFF')
                
                mp_text = Text(
                    f'MP: {attributes.current_mp}/{attributes.max_mp}',
                    position=mp_text_position,
                    scale=mp_text_scale,
                    color=mp_text_color,
                    parent=self.unit_info_panel
                )
                
                # MP bar configuration from master UI config
                mp_bar_config = self.ui_config.get('ui_interface.combat_interface.mp_bar', {})
                mp_bar_model = mp_bar_config.get('model', 'cube')
                mp_bar_width = mp_bar_config.get('width', 0.2)
                mp_bar_height = mp_bar_config.get('height', 0.02)
                mp_bar_bg_position = mp_bar_config.get('bg_position', (0, -0.09, 0.001))
                mp_bar_bg_color = self.ui_config.get_color('ui_interface.combat_interface.mp_bar.bg_color', '#2F2F2F')
                mp_bar_fill_color = self.ui_config.get_color('ui_interface.combat_interface.mp_bar.fill_color', '#0000FF')
                
                mp_bar_bg = Entity(
                    model=mp_bar_model,
                    scale=(mp_bar_width, mp_bar_height, 0.001),
                    color=mp_bar_bg_color,
                    position=mp_bar_bg_position,
                    parent=self.unit_info_panel
                )
                
                mp_bar_fill = Entity(
                    model=mp_bar_model,
                    scale=(mp_bar_width * mp_ratio, mp_bar_height, 0.001),
                    color=mp_bar_fill_color,
                    position=((-mp_bar_width + mp_bar_width * mp_ratio) / 2, -0.09, 0.002),
                    parent=self.unit_info_panel
                )
    
    def _update_available_actions(self):
        """Update which action buttons are available based on AP"""
        if not self.selected_unit:
            # Disable all buttons
            for button in self.action_buttons:
                button.color = color.dark_gray
                button.disabled = True
            return
        
        # Get unit's current AP
        attributes = self.selected_unit.get_component(AttributeStats)
        current_ap = getattr(attributes, 'ap', 0) if attributes else 0
        
        # Check each action button for AP availability
        for button in self.action_buttons:
            action_text = button.text.lower()
            
            # Map button text to action costs
            if action_text == 'move':
                required_ap = ACTION_COSTS.MOVEMENT_MODE_ENTER
            elif action_text == 'attack':
                required_ap = ACTION_COSTS.BASIC_ATTACK
            elif action_text == 'ability':
                required_ap = ACTION_COSTS.BASIC_MAGIC  # Default for abilities
            elif action_text == 'guard':
                required_ap = ACTION_COSTS.GUARD
            elif action_text == 'wait':
                required_ap = ACTION_COSTS.WAIT
            else:
                required_ap = 0  # End Turn and other actions
            
            # Enable/disable button based on AP availability using master UI config
            button_colors = self.ui_config.get('ui_interface.combat_interface.action_buttons.colors', {})
            enabled_color = self.ui_config.get_color_rgba('ui_interface.combat_interface.action_buttons.colors.enabled', (0.3, 0.3, 0.35, 1.0))
            disabled_color = self.ui_config.get_color_rgba('ui_interface.combat_interface.action_buttons.colors.disabled', (0.15, 0.15, 0.15, 1.0))
            
            if current_ap >= required_ap:
                button.color = color.Color(*enabled_color)
                button.disabled = False
            else:
                button.color = color.Color(*disabled_color)
                button.disabled = True
    
    def _on_action_click(self, action: str):
        """Handle action button click"""
        if not self.selected_unit:
            return
        
        # Get unit's current AP
        attributes = self.selected_unit.get_component(AttributeStats)
        current_ap = getattr(attributes, 'ap', 0) if attributes else 0
        
        # Check AP requirement for the action
        action_text = action.lower()
        if action_text == 'move':
            required_ap = ACTION_COSTS.MOVEMENT_MODE_ENTER
        elif action_text == 'attack':
            required_ap = ACTION_COSTS.BASIC_ATTACK
        elif action_text == 'ability':
            required_ap = ACTION_COSTS.BASIC_MAGIC
        elif action_text == 'guard':
            required_ap = ACTION_COSTS.GUARD
        elif action_text == 'wait':
            required_ap = ACTION_COSTS.WAIT
        else:
            required_ap = 0
        
        # Validate AP before executing action
        if current_ap < required_ap:
            print(f"❌ Insufficient AP for {action}: {current_ap}/{required_ap}")
            return
        
        print(f"✅ Action selected: {action} (AP: {current_ap}/{required_ap})")
        
        # This would trigger the appropriate game logic
        # For now, just print the action
    
    def update_turn_order(self, units: List[GameEntity]):
        """Update the turn order display"""
        # Clear existing turn order
        for child in self.turn_order_panel.children:
            destroy(child)
        
        # Turn order configuration from master UI config
        turn_text_config = self.ui_config.get('ui_interface.combat_interface.turn_order_text', {})
        title_position = turn_text_config.get('title_position', (0, 0.15, 0.01))
        title_scale = turn_text_config.get('title_scale', 1.0)
        title_color = self.ui_config.get_color('ui_interface.combat_interface.turn_order_text.title_color', '#FFFFFF')
        title_text = turn_text_config.get('title_text', 'Turn Order')
        
        # Turn order title
        title = Text(
            title_text,
            position=title_position,
            scale=title_scale,
            color=title_color,
            parent=self.turn_order_panel
        )
        
        # Display configuration from master UI config
        max_units_displayed = turn_text_config.get('max_units_displayed', 8)
        unit_start_y = turn_text_config.get('unit_start_y', 0.1)
        unit_spacing = turn_text_config.get('unit_spacing', 0.03)
        unit_scale = turn_text_config.get('unit_scale', 0.7)
        unit_z = turn_text_config.get('unit_z', 0.01)
        
        # Colors from master UI config
        normal_unit_color = self.ui_config.get_color('ui_interface.combat_interface.turn_order_text.normal_color', '#FFFFFF')
        selected_unit_color = self.ui_config.get_color('ui_interface.combat_interface.turn_order_text.selected_color', '#FFFF00')
        
        # Display up to configured number of units in turn order
        for i, unit in enumerate(units[:max_units_displayed]):
            y_pos = unit_start_y - i * unit_spacing
            
            # Highlight current unit
            text_color = selected_unit_color if unit == self.selected_unit else normal_unit_color
            
            unit_text = Text(
                f'{i+1}. Unit {unit.id}',
                position=(0, y_pos, unit_z),
                scale=unit_scale,
                color=text_color,
                parent=self.turn_order_panel
            )
    
    def show_damage_number(self, position, damage: int, damage_type: str = 'physical'):
        """Show floating damage number at position"""
        # This would be handled by the combat animator
        pass
    
    def show_heal_number(self, position, heal: int):
        """Show floating heal number at position"""
        # This would be handled by the combat animator
        pass
    
    def cleanup(self):
        """Clean up interface elements"""
        for element in self.ui_elements:
            if element and hasattr(element, 'destroy'):
                destroy(element)
        
        for button in self.action_buttons:
            if button and hasattr(button, 'destroy'):
                destroy(button)
        
        self.ui_elements.clear()
        self.action_buttons.clear()