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


class CombatInterface:
    """
    Combat UI for turn-based tactical battles.
    
    Provides action buttons, unit information, turn order display,
    and battle status information.
    """
    
    def __init__(self):
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for CombatInterface")
        
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
        """Create the combat interface elements"""
        # Unit info panel (top left)
        self.unit_info_panel = Entity(
            model='cube',
            scale=(0.3, 0.2, 0.01),
            color=color.Color(0.1, 0.1, 0.15, 0.9),
            position=(-0.6, 0.3, 0),
            parent=camera.ui,
            visible=False
        )
        
        # Turn order panel (top right)
        self.turn_order_panel = Entity(
            model='cube', 
            scale=(0.25, 0.4, 0.01),
            color=color.Color(0.1, 0.1, 0.15, 0.9),
            position=(0.6, 0.1, 0),
            parent=camera.ui,
            visible=False
        )
        
        # Action buttons panel (bottom center)
        self._create_action_buttons()
        
        self.ui_elements.extend([self.unit_info_panel, self.turn_order_panel])
    
    def _create_action_buttons(self):
        """Create action buttons for combat"""
        button_y = -0.4
        button_spacing = 0.15
        
        actions = ['Move', 'Attack', 'Ability', 'Guard', 'Wait', 'End Turn']
        
        for i, action in enumerate(actions):
            x_pos = (i - len(actions) / 2 + 0.5) * button_spacing
            
            button = Button(
                text=action,
                position=(x_pos, button_y, 0.01),
                scale=0.08,
                color=color.Color(0.3, 0.3, 0.35, 1.0),
                text_color=color.white,
                parent=camera.ui,
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
        
        # Unit name
        unit_name = Text(
            f'Unit {self.selected_unit.id}',
            position=(0, 0.07, 0.01),
            scale=1.2,
            color=color.white,
            parent=self.unit_info_panel
        )
        
        # Health bar
        attributes = self.selected_unit.get_component(AttributeStats)
        if attributes:
            hp_ratio = attributes.current_hp / attributes.max_hp
            
            hp_text = Text(
                f'HP: {attributes.current_hp}/{attributes.max_hp}',
                position=(0, 0.03, 0.01),
                scale=0.8,
                color=color.white,
                parent=self.unit_info_panel
            )
            
            # Simple health bar representation
            hp_bar_bg = Entity(
                model='cube',
                scale=(0.2, 0.02, 0.001),
                color=color.dark_gray,
                position=(0, -0.01, 0.001),
                parent=self.unit_info_panel
            )
            
            hp_bar_fill = Entity(
                model='cube',
                scale=(0.2 * hp_ratio, 0.02, 0.001),
                color=color.red if hp_ratio < 0.3 else color.yellow if hp_ratio < 0.7 else color.green,
                position=((-0.2 + 0.2 * hp_ratio) / 2, -0.01, 0.002),
                parent=self.unit_info_panel
            )
            
            # MP bar if available
            if attributes.max_mp > 0:
                mp_ratio = attributes.current_mp / attributes.max_mp
                
                mp_text = Text(
                    f'MP: {attributes.current_mp}/{attributes.max_mp}',
                    position=(0, -0.05, 0.01),
                    scale=0.8,
                    color=color.white,
                    parent=self.unit_info_panel
                )
                
                mp_bar_bg = Entity(
                    model='cube',
                    scale=(0.2, 0.02, 0.001),
                    color=color.dark_gray,
                    position=(0, -0.09, 0.001),
                    parent=self.unit_info_panel
                )
                
                mp_bar_fill = Entity(
                    model='cube',
                    scale=(0.2 * mp_ratio, 0.02, 0.001),
                    color=color.blue,
                    position=((-0.2 + 0.2 * mp_ratio) / 2, -0.09, 0.002),
                    parent=self.unit_info_panel
                )
    
    def _update_available_actions(self):
        """Update which action buttons are available"""
        if not self.selected_unit:
            # Disable all buttons
            for button in self.action_buttons:
                button.color = color.dark_gray
                button.disabled = True
            return
        
        # Enable all buttons for now (would check actual availability)
        for button in self.action_buttons:
            button.color = color.Color(0.3, 0.3, 0.35, 1.0)
            button.disabled = False
    
    def _on_action_click(self, action: str):
        """Handle action button click"""
        if not self.selected_unit:
            return
        
        print(f"Action selected: {action}")
        
        # This would trigger the appropriate game logic
        # For now, just print the action
    
    def update_turn_order(self, units: List[GameEntity]):
        """Update the turn order display"""
        # Clear existing turn order
        for child in self.turn_order_panel.children:
            destroy(child)
        
        # Turn order title
        title = Text(
            'Turn Order',
            position=(0, 0.15, 0.01),
            scale=1.0,
            color=color.white,
            parent=self.turn_order_panel
        )
        
        # Display up to 8 units in turn order
        for i, unit in enumerate(units[:8]):
            y_pos = 0.1 - i * 0.03
            
            # Highlight current unit
            text_color = color.yellow if unit == self.selected_unit else color.white
            
            unit_text = Text(
                f'{i+1}. Unit {unit.id}',
                position=(0, y_pos, 0.01),
                scale=0.7,
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