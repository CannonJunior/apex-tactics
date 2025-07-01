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
        
        # Create text elements
        self._create_text_elements()
        
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
        self.unit_info_text = Text('No unit selected')
        self.camera_controls_text = Text('CAMERA: [1] Orbit | [2] Free | [3] Top-down | ACTIVE: Orbit')
        self.game_controls_text = Text('CONTROLS: Click unit to select | Click tile to move | Mouse/WASD for camera')
        self.stats_display_text = Text('')
    
    def _create_action_buttons(self):
        """Create action buttons with callbacks."""
        self.end_turn_btn = Button(
            text='END TURN',
            color=color.orange
        )
        
        # Set up button functionality
        self.end_turn_btn.on_click = self.end_turn_clicked
    
    def _create_carousel_elements(self):
        """Create unit carousel label."""
        self.carousel_label = Text('Turn Order:', parent=camera.ui)
    
    def _create_main_interface(self):
        """Create the main interface with fixed positioning."""
        # Main background panel
        self.panel = Entity(
            model='cube',
            scale=(0.8, 0.25, 0.01),
            color=color.Color(0.1, 0.1, 0.15, 0.9),
            position=(0, -0.3, 0),
            parent=camera.ui
        )
        
        # Position text elements on the panel
        self.unit_info_text.parent = self.panel
        self.unit_info_text.position = (0, 0.08, 0.01)
        self.unit_info_text.scale = 0.8
        
        self.camera_controls_text.parent = self.panel
        self.camera_controls_text.position = (0, 0.04, 0.01)
        self.camera_controls_text.scale = 0.6
        
        self.game_controls_text.parent = self.panel
        self.game_controls_text.position = (0, 0.0, 0.01)
        self.game_controls_text.scale = 0.6
        
        self.stats_display_text.parent = self.panel
        self.stats_display_text.position = (0, -0.04, 0.01)
        self.stats_display_text.scale = 0.6
        
        # Position end turn button
        self.end_turn_btn.parent = self.panel
        self.end_turn_btn.position = (0, -0.08, 0.01)
        self.end_turn_btn.scale = 0.08
    
    def _position_elements(self):
        """Position the interface and carousel elements."""
        # Interface is positioned in _create_main_interface
        
        # Position carousel elements
        self.carousel_label.position = (-0.45, -0.45, 0)
        self.carousel_label.scale = 0.8
    
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
        Create a single unit icon for the carousel.
        
        Args:
            unit: Unit object to create icon for
            index: Position index in carousel
            
        Returns:
            Button: Created unit icon button
        """
        # Calculate position (spacing icons horizontally)
        icon_size = 0.06
        icon_spacing = 0.07
        start_x = -0.3  # Start position
        icon_x = start_x + (index * icon_spacing)
        icon_y = -0.45
        
        # Determine icon color based on unit type and status
        icon_color = self.get_unit_icon_color(unit)
        
        # Create the icon as a clickable button
        unit_icon = Button(
            parent=self.carousel_container,
            model='cube',
            texture='white_cube',
            color=icon_color,
            scale=icon_size,
            position=(icon_x, icon_y, 0)
        )
        
        # Set up click callback
        unit_icon.on_click = lambda u=unit: self.on_unit_icon_clicked(u)
        
        # Store unit reference
        unit_icon.unit = unit
        
        # Add unit name text below icon
        unit_name_text = Text(
            text=unit.name[:4],  # Abbreviate long names
            parent=self.carousel_container,
            position=(icon_x, icon_y - 0.04, 0),
            scale=0.5,
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
            
            # Select the unit in the game
            self.game_reference.active_unit = unit
            
            # Update UI to show selected unit
            self.update_unit_info(unit)
            
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
        if unit:
            # Get weapon info safely
            weapon_name = 'None'
            range_info = 'Range: 0 | Area: 0'
            
            if hasattr(unit, 'equipped_weapon') and unit.equipped_weapon:
                weapon_name = unit.equipped_weapon.get('name', 'Unknown')
            
            if hasattr(unit, 'attack_range') and hasattr(unit, 'attack_effect_area'):
                range_info = f"Range: {unit.attack_range} | Area: {unit.attack_effect_area}"
            
            # Build unit info text with safe attribute access
            unit_name = getattr(unit, 'name', f'Unit {getattr(unit, "id", "Unknown")}')
            unit_type = getattr(unit, 'type', type('obj', (object,), {'value': 'Unknown'})())
            unit_type_name = getattr(unit_type, 'value', 'Unknown') if hasattr(unit_type, 'value') else str(unit_type)
            
            current_mp = getattr(unit, 'current_move_points', 0)
            max_mp = getattr(unit, 'move_points', 0)
            current_hp = getattr(unit, 'hp', 0)
            max_hp = getattr(unit, 'max_hp', 0)
            
            self.unit_info_text.text = f"ACTIVE: {unit_name} ({unit_type_name}) | MP: {current_mp}/{max_mp} | HP: {current_hp}/{max_hp}"
            
            # Build stats display with safe attribute access
            phys_atk = getattr(unit, 'physical_attack', 0)
            mag_atk = getattr(unit, 'magical_attack', 0)
            spir_atk = getattr(unit, 'spiritual_attack', 0)
            phys_def = getattr(unit, 'physical_defense', 0)
            mag_def = getattr(unit, 'magical_defense', 0)
            spir_def = getattr(unit, 'spiritual_defense', 0)
            
            self.stats_display_text.text = f"WEAPON: {weapon_name} | {range_info}\nATK - Physical: {phys_atk} | Magical: {mag_atk} | Spiritual: {spir_atk}\nDEF - Physical: {phys_def} | Magical: {mag_def} | Spiritual: {spir_def}"
        else:
            self.unit_info_text.text = "No unit selected"
            self.stats_display_text.text = ""
        
        # Re-layout after text changes
        # No layout needed for fixed positioning
        
        # Update carousel highlighting
        self.update_carousel_highlighting()
    
    def update_camera_mode(self, mode: int):
        """
        Update the camera mode display.
        
        Args:
            mode: Camera mode (0=Orbit, 1=Free, 2=Top-down)
        """
        mode_names = ["Orbit", "Free", "Top-down"]
        if 0 <= mode < len(mode_names):
            mode_name = mode_names[mode]
            self.camera_controls_text.text = f"CAMERA: [1] Orbit | [2] Free | [3] Top-down | ACTIVE: {mode_name}"
            
            # Re-layout after text changes
            # No layout needed for fixed positioning
    
    def set_controls_text(self, controls_text: str):
        """
        Update the game controls text.
        
        Args:
            controls_text: New controls text to display
        """
        self.game_controls_text.text = controls_text
        # No layout needed for fixed positioning
    
    def toggle_visibility(self):
        """Toggle the visibility of the control panel."""
        if hasattr(self, 'panel') and self.panel:
            self.panel.enabled = not self.panel.enabled
            # Toggle carousel visibility too
            self.carousel_label.enabled = self.panel.enabled
            self.carousel_container.enabled = self.panel.enabled
            status = "shown" if self.panel.enabled else "hidden"
            print(f"Character Attack Interface {status}")
    
    def show(self):
        """Show the character attack interface."""
        if hasattr(self, 'panel') and self.panel:
            self.panel.enabled = True
            self.carousel_label.enabled = True
            self.carousel_container.enabled = True
    
    def hide(self):
        """Hide the character attack interface."""
        if hasattr(self, 'panel') and self.panel:
            self.panel.enabled = False
            self.carousel_label.enabled = False
            self.carousel_container.enabled = False
    
    def is_visible(self) -> bool:
        """Check if the character attack interface is currently visible."""
        if hasattr(self, 'panel') and self.panel:
            return self.panel.enabled
        return False
    
    def cleanup(self):
        """Clean up all interface resources."""
        self.cleanup_carousel()
        if hasattr(self, 'panel') and self.panel:
            destroy(self.panel)
        if hasattr(self, 'unit_info_text') and self.unit_info_text:
            destroy(self.unit_info_text)
        if hasattr(self, 'camera_controls_text') and self.camera_controls_text:
            destroy(self.camera_controls_text)
        if hasattr(self, 'game_controls_text') and self.game_controls_text:
            destroy(self.game_controls_text)
        if hasattr(self, 'stats_display_text') and self.stats_display_text:
            destroy(self.stats_display_text)
        if hasattr(self, 'end_turn_btn') and self.end_turn_btn:
            destroy(self.end_turn_btn)
