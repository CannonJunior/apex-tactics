"""
UI Manager

Manages UI elements extracted from monolithic controller including:
- Health bars and resource bars for active units
- Hotkey slots for abilities (1-8 keys)
- Targeted unit bars for area effects
- Unit carousel for turn order display
- UI synchronization with game state

Features:
- Dynamic health/resource bar creation and updating
- Configurable hotkey slot system with visual feedback
- Multi-unit targeting UI support
- UI style management integration
- Event-driven UI updates
"""

from typing import List, Dict, Optional, Any, Callable
import json

try:
    from ursina import Button, Text, camera, color, destroy
    from ursina.prefabs.health_bar import HealthBar
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False

from core.models.unit import Unit
from game.interfaces.game_interfaces import IUIManager
from ui.core.ui_style_manager import get_ui_style_manager


class MockHotkeySlot:
    """Mock hotkey slot for testing without Ursina."""
    def __init__(self):
        self.ability_data = None
        self.enabled = True
        self.text = ""
        self.eternal = False  # For Ursina compatibility


class UIManager(IUIManager):
    """
    Manages tactical RPG UI elements.
    
    Extracted from monolithic TacticalRPG controller to provide
    clean separation of UI management concerns.
    """
    
    def __init__(self):
        """Initialize UI manager."""
        # Check for test mode
        import os
        self.test_mode = os.environ.get('APEX_TEST_MODE') == '1'
        
        if not URSINA_AVAILABLE and not self.test_mode:
            raise ImportError("Ursina is required for UIManager")
        
        # Health and resource bars for active unit
        self.health_bar: Optional[HealthBar] = None
        self.health_bar_label: Optional[Text] = None
        self.resource_bar: Optional[HealthBar] = None
        self.resource_bar_label: Optional[Text] = None
        
        # Hotkey system
        self.hotkey_slots: List[Button] = []
        self.hotkey_config: Optional[Dict[str, Any]] = None
        
        # Targeted unit bars (for area effects)
        self.targeted_health_bars: List[HealthBar] = []
        self.targeted_health_bar_labels: List[Text] = []
        self.targeted_resource_bars: List[HealthBar] = []
        self.targeted_resource_bar_labels: List[Text] = []
        
        # Unit carousel (turn order display)
        self.unit_carousel_buttons: List[Button] = []
        self.carousel_visible = False
        
        # UI state
        self.current_unit: Optional[Unit] = None
        self.style_manager = get_ui_style_manager()
        
        # Event callbacks
        self.on_hotkey_activated: List[Callable] = []
        self.on_unit_selected: List[Callable] = []
        
        # Initialize systems
        self._load_hotkey_config()
        if not self.test_mode:
            self._create_hotkey_slots()
        else:
            # Initialize empty slots for test mode
            self.hotkey_slots = [MockHotkeySlot() for _ in range(8)]
        
        print("✅ UIManager initialized")
    
    def update_unit_bars(self, unit: Optional[Unit]):
        """
        Update health and resource bars for the specified unit.
        
        Args:
            unit: Unit to display bars for, or None to hide bars
        """
        self.current_unit = unit
        self._update_health_bar(unit)
        self._update_resource_bar(unit)
    
    def _update_health_bar(self, unit: Optional[Unit]):
        """Create or update health bar for the unit."""
        if self.test_mode:
            # Mock behavior for testing
            return
            
        # Clear existing health bar
        if self.health_bar:
            self.health_bar.enabled = False
            self.health_bar = None
        
        if self.health_bar_label:
            self.health_bar_label.enabled = False
            self.health_bar_label = None
        
        if unit:
            # Create health bar label
            self.health_bar_label = Text(
                text="HP",
                parent=camera.ui,
                position=(-0.47, 0.45),
                scale=1.0,
                color=self.style_manager.get_bar_label_color(),
                origin=(-0.5, 0)
            )
            
            # Create health bar
            self.health_bar = HealthBar(
                max_value=unit.max_hp,
                value=unit.hp,
                position=(-0.4, 0.45),
                parent=camera.ui,
                scale=(0.3, 0.03),
                color=self.style_manager.get_health_bar_bg_color()
            )
            
            # Set foreground bar color
            if hasattr(self.health_bar, 'bar'):
                self.health_bar.bar.color = self.style_manager.get_health_bar_color()
            
            print(f"💖 Health bar updated: {unit.name} ({unit.hp}/{unit.max_hp})")
    
    def _update_resource_bar(self, unit: Optional[Unit]):
        """Create or update resource bar for the unit."""
        if self.test_mode:
            return
            
        # Clear existing resource bar
        if self.resource_bar:
            self.resource_bar.enabled = False
            self.resource_bar = None
        
        if self.resource_bar_label:
            self.resource_bar_label.enabled = False
            self.resource_bar_label = None
        
        if unit:
            # Get resource information
            resource_type = unit.primary_resource_type
            resource_value = unit.get_primary_resource_value()
            resource_max = unit.get_primary_resource_max()
            
            # Get styling from style manager
            bar_color = self.style_manager.get_resource_bar_color(resource_type)
            label_text = self.style_manager.get_resource_bar_label(resource_type)
            
            # Create resource bar label
            self.resource_bar_label = Text(
                text=label_text,
                parent=camera.ui,
                position=(-0.47, 0.4),
                scale=1.0,
                color=self.style_manager.get_bar_label_color(),
                origin=(-0.5, 0)
            )
            
            # Create resource bar
            self.resource_bar = HealthBar(
                max_value=resource_max,
                value=resource_value,
                position=(-0.4, 0.4),
                parent=camera.ui,
                scale=(0.3, 0.03),
                color=self.style_manager.get_resource_bar_bg_color()
            )
            
            # Set foreground bar color
            if hasattr(self.resource_bar, 'bar'):
                self.resource_bar.bar.color = bar_color
            
            print(f"⚡ Resource bar updated: {unit.name} ({resource_value}/{resource_max} {resource_type})")
    
    def update_hotkey_slots(self, abilities: List[Dict[str, Any]]):
        """
        Update hotkey slot displays with unit abilities.
        
        Args:
            abilities: List of ability data dictionaries
        """
        if not self.hotkey_slots:
            return
        
        # Clear existing ability data
        for slot in self.hotkey_slots:
            slot.ability_data = None
            slot.color = self._get_empty_slot_color()
            slot.enabled = False
            
            # Clear ability text if exists
            if hasattr(slot, 'ability_text'):
                destroy(slot.ability_text)
                slot.ability_text = None
        
        # Update slots with new abilities
        for i, ability in enumerate(abilities[:len(self.hotkey_slots)]):
            slot = self.hotkey_slots[i]
            slot.ability_data = ability
            slot.enabled = True
            
            # Set slot color based on ability type
            slot.color = self._get_ability_color(ability.get('type', 'physical'))
            
            # Add ability name text
            if ability.get('name'):
                slot.ability_text = Text(
                    text=ability['name'][:3].upper(),  # First 3 letters
                    parent=slot,
                    position=(0, -0.02, -0.01),
                    scale=0.2,
                    color=color.white,
                    origin=(0, 0)
                )
        
        print(f"🎮 Hotkey slots updated: {len(abilities)} abilities")
    
    def show_targeted_bars(self, units: List[Unit]):
        """
        Show health/resource bars for targeted units.
        
        Args:
            units: List of units to show bars for
        """
        # Clear existing targeted bars
        self._clear_targeted_bars()
        
        # Create bars for each targeted unit
        for i, unit in enumerate(units[:4]):  # Limit to 4 targets for UI space
            y_offset = 0.3 - (i * 0.1)  # Stack vertically
            
            # Health bar
            health_bar = HealthBar(
                max_value=unit.max_hp,
                value=unit.hp,
                position=(-0.4, y_offset),
                parent=camera.ui,
                scale=(0.2, 0.02),
                color=self.style_manager.get_health_bar_bg_color()
            )
            
            if hasattr(health_bar, 'bar'):
                health_bar.bar.color = self.style_manager.get_health_bar_color()
            
            # Health bar label
            health_label = Text(
                text=f"{unit.name}",
                parent=camera.ui,
                position=(-0.6, y_offset),
                scale=0.8,
                color=self.style_manager.get_bar_label_color(),
                origin=(-0.5, 0)
            )
            
            self.targeted_health_bars.append(health_bar)
            self.targeted_health_bar_labels.append(health_label)
        
        print(f"🎯 Targeted bars shown for {len(units)} units")
    
    def hide_all_bars(self):
        """Hide all UI bars."""
        self.update_unit_bars(None)
        self._clear_targeted_bars()
        self._hide_hotkey_slots()
    
    def show_unit_carousel(self, units: List[Unit], current_unit_index: int = 0):
        """
        Show unit carousel with turn order.
        
        Args:
            units: List of units in turn order
            current_unit_index: Index of currently active unit
        """
        # Clear existing carousel
        self._clear_unit_carousel()
        
        # Create carousel buttons
        for i, unit in enumerate(units[:8]):  # Limit to 8 units for UI space
            x_offset = -0.8 + (i * 0.2)  # Horizontal layout
            
            # Determine button color based on unit state
            if i == current_unit_index:
                button_color = color.yellow  # Active unit
            elif unit.team == 'player':
                button_color = color.blue   # Player unit
            else:
                button_color = color.red    # Enemy unit
            
            # Create unit button
            unit_button = Button(
                parent=camera.ui,
                model='cube',
                color=button_color,
                scale=0.08,
                position=(x_offset, -0.45, 0),
                on_click=lambda unit=unit: self._on_unit_carousel_clicked(unit)
            )
            
            # Add unit name text
            unit_text = Text(
                text=unit.name[:3].upper(),
                parent=unit_button,
                position=(0, 0, -0.01),
                scale=0.3,
                color=color.white,
                origin=(0, 0)
            )
            
            unit_button.unit = unit
            unit_button.unit_text = unit_text
            self.unit_carousel_buttons.append(unit_button)
        
        self.carousel_visible = True
        print(f"🎠 Unit carousel shown: {len(units)} units")
    
    def hide_unit_carousel(self):
        """Hide the unit carousel."""
        self._clear_unit_carousel()
        self.carousel_visible = False
    
    def sync_ui_state(self):
        """Synchronize UI with current game state."""
        # Refresh current unit bars
        if self.current_unit:
            self._update_health_bar(self.current_unit)
            self._update_resource_bar(self.current_unit)
        
        print("🔄 UI state synchronized")
    
    def refresh_unit_health(self, unit: Unit):
        """Refresh health bar if the unit is currently displayed."""
        if self.current_unit and self.current_unit == unit and self.health_bar:
            self.health_bar.value = unit.hp
    
    def refresh_unit_resources(self, unit: Unit):
        """Refresh resource bar if the unit is currently displayed."""
        if self.current_unit and self.current_unit == unit and self.resource_bar:
            resource_value = unit.get_primary_resource_value()
            self.resource_bar.value = resource_value
    
    # === Private Helper Methods ===
    
    def _load_hotkey_config(self):
        """Load hotkey configuration from data files."""
        try:
            # This is a placeholder - in real implementation would load from JSON
            self.hotkey_config = {
                'hotkey_system': {
                    'max_interface_slots': 8,
                    'slot_layout': {
                        'slot_size': 0.06,
                        'slot_spacing': 0.01,
                        'start_position': {'x': -0.4, 'y': 0.35, 'z': 0}
                    },
                    'visual_settings': {
                        'empty_slot_color': '#404040',
                        'physical_color': '#ff4444',
                        'magical_color': '#4444ff',
                        'spiritual_color': '#44ff44',
                        'hotkey_text_color': '#ffff00',
                        'hotkey_text_scale': 0.3
                    },
                    'display_options': {
                        'show_hotkey_numbers': True
                    }
                }
            }
        except Exception as e:
            print(f"⚠️ Could not load hotkey config: {e}")
            self.hotkey_config = {}
    
    def _create_hotkey_slots(self):
        """Create hotkey ability slots."""
        if not self.hotkey_config:
            return
        
        hotkey_settings = self.hotkey_config.get('hotkey_system', {})
        slot_layout = hotkey_settings.get('slot_layout', {})
        visual_settings = hotkey_settings.get('visual_settings', {})
        
        # Configuration values
        max_slots = hotkey_settings.get('max_interface_slots', 8)
        slot_size = slot_layout.get('slot_size', 0.06)
        slot_spacing = slot_layout.get('slot_spacing', 0.01)
        start_pos = slot_layout.get('start_position', {'x': -0.4, 'y': 0.35, 'z': 0})
        
        empty_color = self._hex_to_color(visual_settings.get('empty_slot_color', '#404040'))
        
        # Clear existing slots
        self._clear_hotkey_slots()
        
        # Create slots
        for i in range(max_slots):
            x_offset = i * (slot_size + slot_spacing)
            
            slot_button = Button(
                parent=camera.ui,
                model='cube',
                color=empty_color,
                scale=slot_size,
                position=(start_pos['x'] + x_offset, start_pos['y'], start_pos['z']),
                on_click=lambda slot_index=i: self._on_hotkey_slot_clicked(slot_index)
            )
            
            # Add hotkey number text
            if hotkey_settings.get('display_options', {}).get('show_hotkey_numbers', True):
                hotkey_text_color = self._hex_to_color(visual_settings.get('hotkey_text_color', '#ffff00'))
                hotkey_text_scale = visual_settings.get('hotkey_text_scale', 0.3)
                
                hotkey_text = Text(
                    text=str(i + 1),
                    parent=slot_button,
                    position=(0, 0, -0.01),
                    scale=hotkey_text_scale,
                    color=hotkey_text_color,
                    origin=(0, 0)
                )
                slot_button.hotkey_text = hotkey_text
            
            slot_button.ability_data = None
            slot_button.slot_index = i
            slot_button.enabled = False
            
            self.hotkey_slots.append(slot_button)
    
    def _clear_hotkey_slots(self):
        """Clear existing hotkey slots."""
        if self.test_mode:
            # In test mode, just clear the list
            self.hotkey_slots.clear()
        else:
            # In normal mode, destroy Ursina entities
            for slot in self.hotkey_slots:
                if hasattr(slot, 'hotkey_text'):
                    destroy(slot.hotkey_text)
                if hasattr(slot, 'ability_text'):
                    destroy(slot.ability_text)
                destroy(slot)
            self.hotkey_slots.clear()
    
    def _hide_hotkey_slots(self):
        """Hide hotkey slots."""
        for slot in self.hotkey_slots:
            slot.enabled = False
    
    def _show_hotkey_slots(self):
        """Show hotkey slots."""
        for slot in self.hotkey_slots:
            if slot.ability_data:
                slot.enabled = True
    
    def _clear_targeted_bars(self):
        """Clear targeted unit bars."""
        for bar in self.targeted_health_bars:
            try:
                destroy(bar)
            except:
                pass
        
        for label in self.targeted_health_bar_labels:
            try:
                destroy(label)
            except:
                pass
        
        self.targeted_health_bars.clear()
        self.targeted_health_bar_labels.clear()
    
    def _clear_unit_carousel(self):
        """Clear unit carousel buttons."""
        for button in self.unit_carousel_buttons:
            if hasattr(button, 'unit_text'):
                destroy(button.unit_text)
            destroy(button)
        self.unit_carousel_buttons.clear()
    
    def _hex_to_color(self, hex_color: str):
        """Convert hex color string to Ursina color."""
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            return color.rgb(r, g, b)
        except:
            return color.gray
    
    def _get_empty_slot_color(self):
        """Get color for empty hotkey slots."""
        return self._hex_to_color('#404040')
    
    def _get_ability_color(self, ability_type: str):
        """Get color for ability type."""
        color_map = {
            'physical': self._hex_to_color('#ff4444'),
            'magical': self._hex_to_color('#4444ff'),
            'spiritual': self._hex_to_color('#44ff44')
        }
        return color_map.get(ability_type, self._hex_to_color('#cccccc'))
    
    def _on_hotkey_slot_clicked(self, slot_index: int):
        """Handle hotkey slot click."""
        for callback in self.on_hotkey_activated:
            try:
                callback(slot_index)
            except Exception as e:
                print(f"⚠️ Hotkey callback error: {e}")
    
    def _on_unit_carousel_clicked(self, unit: Unit):
        """Handle unit carousel click."""
        for callback in self.on_unit_selected:
            try:
                callback(unit)
            except Exception as e:
                print(f"⚠️ Unit selection callback error: {e}")
    
    # === Event Callback Registration ===
    
    def add_hotkey_callback(self, callback: Callable):
        """Add callback for hotkey activation."""
        self.on_hotkey_activated.append(callback)
    
    def add_unit_selection_callback(self, callback: Callable):
        """Add callback for unit selection from carousel."""
        self.on_unit_selected.append(callback)
    
    def get_ui_state(self) -> Dict[str, Any]:
        """Get comprehensive UI state information."""
        return {
            "current_unit": self.current_unit.name if self.current_unit else None,
            "health_bar_active": self.health_bar is not None,
            "resource_bar_active": self.resource_bar is not None,
            "hotkey_slots": len([s for s in self.hotkey_slots if s.enabled]),
            "targeted_bars": len(self.targeted_health_bars),
            "carousel_visible": self.carousel_visible,
            "carousel_units": len(self.unit_carousel_buttons)
        }
    
    def shutdown(self):
        """Clean shutdown of UI manager."""
        self.hide_all_bars()
        self.hide_unit_carousel()
        self._clear_hotkey_slots()
        
        # Clear callbacks
        self.on_hotkey_activated.clear()
        self.on_unit_selected.clear()
        
        print("✅ UIManager shutdown complete")