"""
Character Attack Interface

Main UI interface showing unit info, camera controls, action buttons, and unit carousel.
Non-draggable interface styled consistently with other game interfaces.
"""

from typing import Optional, Any, List

try:
    from ursina import *
    from ursina import Panel, Entity, Text, Button, color, camera, destroy
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False

# Import UnitType enum and data manager
from core.models.unit_types import UnitType
from core.assets.unit_data_manager import get_unit_data_manager
from core.assets.config_manager import get_config_manager


class CharacterAttackInterface:
    """
    Character Attack Interface for tactical RPG games.
    
    Features:
    - Current unit information and stats
    - Camera control instructions
    - Game control instructions  
    - Action buttons (End Turn)
    - Unit carousel showing turn order
    - Interactive unit selection via carousel
    - Fixed positioning like other interfaces
    """
    
    def __init__(self, game_reference: Optional[Any] = None):
        """
        Initialize character attack interface.
        
        Args:
            game_reference: Optional reference to main game object for button callbacks
        """
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for CharacterAttackInterface")
            
        self.game_reference = game_reference
        
        # Unit carousel variables
        self.unit_carousel_icons: List[Button] = []
        self.carousel_container = Entity(parent=camera.ui)
        
        # Text elements removed
        # self._create_text_elements()
        
        # Create action buttons
        self._create_action_buttons()
        
        # Create carousel elements
        self._create_carousel_elements()
        
        # Create main interface
        self._create_main_interface()
        
        # Position panel and carousel
        self._position_elements()
    
    def _create_text_elements(self):
        """Create all text display elements."""
        # Text elements removed per user request
        pass
    
    def _create_action_buttons(self):
        """Create action buttons with callbacks."""
        # Load master UI configuration for end turn button
        try:
            from src.core.ui.ui_config_manager import get_ui_config_manager
            ui_config = get_ui_config_manager()
            
            # Get button configuration from master UI config
            btn_color = ui_config.get_color('panels.control_panel.end_turn_button.color', '#FFA500')
            btn_text = ui_config.get('panels.control_panel.end_turn_button.text', 'END TURN')
            
            self.end_turn_btn = Button(
                text=btn_text,
                color=btn_color
            )
        except ImportError:
            # Fallback if master UI config not available
            self.end_turn_btn = Button(
                text='END TURN',
                color=color.orange
            )
        
        # Set up button functionality
        self.end_turn_btn.on_click = self.end_turn_clicked
    
    def _create_carousel_elements(self):
        """Create unit carousel label using configuration."""
        config = get_config_manager()
        carousel_text = config.get_value('ui_layout.ui_layout.control_panel.carousel.label.text', 'Turn Order:')
        self.carousel_label = Text(carousel_text, parent=camera.ui)
    
    def _create_main_interface(self):
        """Create the main interface using configuration values."""
        # Main background panel removed per user request
        self.panel = None
        
        # Position end turn button independently (no panel parent)
        self.end_turn_btn.parent = camera.ui
        
        # Load position and scale from master UI config
        try:
            from src.core.ui.ui_config_manager import get_ui_config_manager
            ui_config = get_ui_config_manager()
            
            # Get button position and scale from master UI config
            btn_pos = ui_config.get_position_tuple('panels.control_panel.end_turn_button.position', (0, -0.38, 0.01))
            btn_scale = ui_config.get('panels.control_panel.end_turn_button.scale', 0.08)
            
            self.end_turn_btn.position = btn_pos
            self.end_turn_btn.scale = btn_scale
        except ImportError:
            # Fallback if master UI config not available
            config = get_config_manager()
            btn_pos = config.get_scale('ui_layout.ui_layout.control_panel.end_turn_button.position', (0, -0.38, 0.01))
            btn_scale = config.get_value('ui_layout.ui_layout.control_panel.end_turn_button.scale', 0.08)
            self.end_turn_btn.position = btn_pos
            self.end_turn_btn.scale = btn_scale
    
    def _position_elements(self):
        """Position the interface and carousel elements using configuration."""
        # Interface is positioned in _create_main_interface
        
        # Position carousel elements using configuration
        config = get_config_manager()
        carousel_pos = config.get_scale('ui_layout.ui_layout.control_panel.carousel.label.position', (-0.45, -0.45, 0))
        carousel_scale = config.get_value('ui_layout.ui_layout.control_panel.carousel.label.scale', 0.8)
        self.carousel_label.position = carousel_pos
        self.carousel_label.scale = carousel_scale
    
    def end_turn_clicked(self):
        """Handle End Turn button click."""
        print("End Turn button clicked!")
        if hasattr(self, 'game_reference') and self.game_reference:
            self.game_reference.end_current_turn()
    
    
    def set_game_reference(self, game: Any):
        """
        Set reference to the main game object for button interactions.
        
        Args:
            game: Main game object with action methods
        """
        self.game_reference = game
        # Initialize carousel with game units
        if game and hasattr(game, 'turn_manager') and game.turn_manager:
            self.create_unit_carousel()
    
    def create_unit_carousel(self):
        """Create carousel of unit icons in turn order."""
        if not self.game_reference or not self.game_reference.turn_manager:
            return
        
        # Clear existing carousel
        self.clear_carousel()
        
        # Get units in turn order
        units_in_order = self.game_reference.turn_manager.units
        
        # Create icon for each unit
        for i, unit in enumerate(units_in_order):
            unit_icon = self.create_unit_icon(unit, i)
            self.unit_carousel_icons.append(unit_icon)
        
        print(f"Created unit carousel with {len(self.unit_carousel_icons)} units")
    
    def create_unit_icon(self, unit: Any, index: int) -> Button:
        """
        Create a single unit icon for the carousel using master UI configuration.
        
        Args:
            unit: Unit object to create icon for
            index: Position index in carousel
            
        Returns:
            Button: Created unit icon button
        """
        # Use master UI configuration
        from src.core.ui.ui_config_manager import get_ui_config_manager
        ui_config = get_ui_config_manager()
        
        # Get carousel configuration from master config
        icon_size = ui_config.get('panels.control_panel.unit_carousel.icons.size', 0.06)
        icon_spacing = ui_config.get('panels.control_panel.unit_carousel.icons.spacing', 0.07)
        start_x = ui_config.get('panels.control_panel.unit_carousel.icons.start_x', -0.3)
        icon_y = ui_config.get('panels.control_panel.unit_carousel.icons.y_position', -0.45)
        
        # Calculate position (spacing icons horizontally)
        icon_x = start_x + (index * icon_spacing)
        
        # Determine icon color based on unit type and status
        icon_color = self.get_unit_icon_color(unit)
        
        # Create the icon as a clickable button using master config
        unit_icon = Button(
            parent=self.carousel_container,
            model=ui_config.get('models_and_textures.default_models.button', 'cube'),
            texture=ui_config.get('models_and_textures.default_textures.button', 'white_cube'),
            color=icon_color,
            scale=icon_size,
            position=(icon_x, icon_y, 0)
        )
        
        # Set up click callback
        unit_icon.on_click = lambda u=unit: self.on_unit_icon_clicked(u)
        
        # Store unit reference
        unit_icon.unit = unit
        
        # Add unit name text below icon using master config
        name_text_scale = ui_config.get('panels.control_panel.unit_carousel.icons.name_text_scale', 0.5)
        name_text_offset = ui_config.get('panels.control_panel.unit_carousel.icons.name_text_offset', -0.04)
        
        unit_name_text = Text(
            text=unit.name[:4],  # Abbreviate long names
            parent=self.carousel_container,
            position=(icon_x, icon_y + name_text_offset, 0),
            scale=name_text_scale,
            origin=(0, 0)
        )
        
        # Store text reference for cleanup
        unit_icon.name_text = unit_name_text
        
        return unit_icon
    
    def get_unit_icon_color(self, unit: Any) -> color:
        """
        Get color for unit icon based on unit type and status.
        
        Args:
            unit: Unit object to get color for
            
        Returns:
            color: Ursina color for the unit icon
        """
        # Current turn unit gets special highlighting
        if (self.game_reference and 
            self.game_reference.turn_manager and 
            self.game_reference.turn_manager.current_unit() == unit):
            return color.yellow
        
        # Get color from centralized data manager
        data_manager = get_unit_data_manager()
        base_color = data_manager.get_unit_color(unit.type)
        
        # Dim color if unit is low on health
        if unit.hp < unit.max_hp * 0.3:
            return color.rgb(base_color.r * 0.5, base_color.g * 0.5, base_color.b * 0.5)
        
        return base_color
    
    def create_unit_tooltip(self, unit: Any) -> str:
        """
        Create tooltip text for unit icon.
        
        Args:
            unit: Unit object to create tooltip for
            
        Returns:
            str: Formatted tooltip text
        """
        weapon_name = unit.equipped_weapon['name'] if unit.equipped_weapon else 'None'
        tooltip_text = f"{unit.name} ({unit.type.value})\n"
        tooltip_text += f"HP: {unit.hp}/{unit.max_hp}\n"
        tooltip_text += f"MP: {unit.current_move_points}/{unit.move_points}\n"
        tooltip_text += f"Weapon: {weapon_name}"
        return tooltip_text
    
    def on_unit_icon_clicked(self, unit: Any):
        """
        Handle clicking on a unit icon.
        
        Args:
            unit: Unit that was clicked
        """
        if self.game_reference:
            print(f"Unit icon clicked: {unit.name}")
            
            # Use centralized method for consistent behavior
            self.game_reference.set_active_unit(unit, update_highlights=True, update_ui=True)
            
            # Highlight the unit on the battlefield
            if hasattr(self.game_reference, 'clear_highlights'):
                self.game_reference.clear_highlights()
            if hasattr(self.game_reference, 'highlight_active_unit'):
                self.game_reference.highlight_active_unit()
            if hasattr(self.game_reference, 'highlight_movement_range'):
                self.game_reference.highlight_movement_range()
            
            # Update carousel to reflect current selection
            self.update_carousel_highlighting()
            
            # Update health bar and resource bar for selected unit
            if hasattr(self.game_reference, 'update_health_bar'):
                self.game_reference.update_health_bar(unit)
            if hasattr(self.game_reference, 'update_resource_bar'):
                self.game_reference.update_resource_bar(unit)
    
    def update_carousel_highlighting(self):
        """Update carousel icon highlighting to show current turn and selection."""
        if not self.unit_carousel_icons or not self.game_reference:
            return
        
        current_turn_unit = None
        if self.game_reference.turn_manager:
            current_turn_unit = self.game_reference.turn_manager.current_unit()
        
        active_unit = self.game_reference.active_unit
        
        for icon in self.unit_carousel_icons:
            unit = icon.unit
            
            # Determine icon color
            if unit == current_turn_unit:
                icon.color = color.yellow  # Current turn
            elif unit == active_unit:
                icon.color = color.white   # Selected
            else:
                icon.color = self.get_unit_icon_color(unit)  # Default
    
    def clear_carousel(self):
        """Clear all carousel icons."""
        for icon in self.unit_carousel_icons:
            if hasattr(icon, 'name_text'):
                destroy(icon.name_text)
            destroy(icon)
        self.unit_carousel_icons.clear()
    
    def update_carousel(self):
        """Update carousel when units or turn order changes."""
        if self.game_reference and self.game_reference.turn_manager:
            self.create_unit_carousel()
    
    def cleanup_carousel(self):
        """Clean up carousel resources."""
        self.clear_carousel()
        if self.carousel_container:
            destroy(self.carousel_container)
        if self.carousel_label:
            destroy(self.carousel_label)
    
    def update_unit_info(self, unit: Optional[Any]):
        """
        Update the unit information display.
        
        Args:
            unit: Unit object to display info for, or None to clear
        """
        # Text display removed per user request
        # Update carousel highlighting
        self.update_carousel_highlighting()
    
    def update_camera_mode(self, mode: int):
        """
        Update the camera mode display.
        
        Args:
            mode: Camera mode (0=Orbit, 1=Free, 2=Top-down)
        """
        # Camera mode display removed per user request
        pass
    
    def set_controls_text(self, controls_text: str):
        """
        Update the game controls text.
        
        Args:
            controls_text: New controls text to display
        """
        # Game controls text display removed per user request
        pass
    
    def toggle_visibility(self):
        """Toggle the visibility of the control panel."""
        # Toggle end turn button and carousel visibility
        if hasattr(self, 'end_turn_btn') and self.end_turn_btn:
            self.end_turn_btn.enabled = not self.end_turn_btn.enabled
            # Toggle carousel visibility too
            self.carousel_label.enabled = self.end_turn_btn.enabled
            self.carousel_container.enabled = self.end_turn_btn.enabled
            status = "shown" if self.end_turn_btn.enabled else "hidden"
            print(f"Character Attack Interface {status}")
    
    def show(self):
        """Show the character attack interface."""
        if hasattr(self, 'end_turn_btn') and self.end_turn_btn:
            self.end_turn_btn.enabled = True
            self.carousel_label.enabled = True
            self.carousel_container.enabled = True
    
    def hide(self):
        """Hide the character attack interface."""
        if hasattr(self, 'end_turn_btn') and self.end_turn_btn:
            self.end_turn_btn.enabled = False
            self.carousel_label.enabled = False
            self.carousel_container.enabled = False
    
    def is_visible(self) -> bool:
        """Check if the character attack interface is currently visible."""
        if hasattr(self, 'end_turn_btn') and self.end_turn_btn:
            return self.end_turn_btn.enabled
        return False
    
    def cleanup(self):
        """Clean up all interface resources."""
        self.cleanup_carousel()
        # Panel removed per user request
        # Text elements removed per user request
        if hasattr(self, 'end_turn_btn') and self.end_turn_btn:
            destroy(self.end_turn_btn)
