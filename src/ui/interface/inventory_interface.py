"""
Modal Inventory Interface

Sophisticated inventory management interface with equipment visualization,
stat comparison, and real-time feedback.
"""

from typing import Dict, List, Optional, Any, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from ursina import Entity
from enum import Enum
from dataclasses import dataclass

try:
    from ursina import Entity, Text, Button, color, camera, scene, destroy
    from ursina import Panel, ButtonGroup, Slider, CheckBox
    from ursina.prefabs.dropdown_menu import DropdownMenu
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False

from core.ecs.entity import Entity as GameEntity
from components.equipment.equipment import EquipmentComponent, EquipmentTier, EquipmentType
from components.stats.attributes import AttributeStats


class InterfaceMode(Enum):
    """Different modes for the inventory interface"""
    INVENTORY = "inventory"
    EQUIPMENT = "equipment" 
    COMPARISON = "comparison"
    CRAFTING = "crafting"


@dataclass
class StatChange:
    """Represents a change in a stat value"""
    stat_name: str
    old_value: int
    new_value: int
    
    @property
    def change(self) -> int:
        return self.new_value - self.old_value
    
    @property
    def is_improvement(self) -> bool:
        return self.change > 0


class InventoryInterface:
    """
    Modal inventory interface for equipment management.
    
    Provides comprehensive inventory management with real-time stat calculations,
    equipment comparison, and visual feedback for all changes.
    """
    
    def __init__(self, screen_width: int = 1920, screen_height: int = 1080):
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for InventoryInterface")
        
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Interface state
        self.is_visible = False
        self.current_mode = InterfaceMode.INVENTORY
        self.selected_unit: Optional[GameEntity] = None
        self.selected_item: Optional[EquipmentComponent] = None
        self.comparison_item: Optional[EquipmentComponent] = None
        
        # UI components
        self.main_panel: Optional['Entity'] = None
        self.inventory_grid: List[List['Entity']] = []
        self.equipment_slots: Dict[EquipmentSlot, 'Entity'] = {}
        self.stat_displays: Dict[str, 'Entity'] = {}
        self.comparison_displays: Dict[str, 'Entity'] = {}
        
        # Interface elements
        self.ui_elements: List['Entity'] = []
        self.modal_background: Optional['Entity'] = None
        
        # Layout configuration
        self.panel_width = 0.8
        self.panel_height = 0.9
        self.grid_size = (8, 6)  # 8x6 inventory grid
        
        # Color scheme
        self.colors = {
            'background': color.Color(0.1, 0.1, 0.15, 0.95),
            'panel': color.Color(0.2, 0.2, 0.25, 0.9),
            'button': color.Color(0.3, 0.3, 0.35, 1.0),
            'button_hover': color.Color(0.4, 0.4, 0.45, 1.0),
            'text': color.white,
            'stat_increase': color.green,
            'stat_decrease': color.red,
            'equipment_common': color.white,
            'equipment_enhanced': color.Color(0.0, 1.0, 0.0, 1.0),  # Green
            'equipment_enchanted': color.Color(0.0, 0.7, 1.0, 1.0),  # Blue
            'equipment_superpowered': color.Color(0.8, 0.0, 1.0, 1.0),  # Purple
            'equipment_metapowered': color.Color(1.0, 0.7, 0.0, 1.0)   # Orange/Gold
        }
        
        # Initialize interface
        self._create_interface()
    
    def _create_interface(self):
        """Create the main interface components"""
        # Modal background (invisible clickable area)
        self.modal_background = Entity(
            model='cube',
            scale=(20, 20, 1),
            color=color.Color(0, 0, 0, 0.3),
            position=(0, 0, -1),
            parent=camera.ui,
            visible=False
        )
        
        # Main panel
        self.main_panel = Entity(
            model='cube',
            scale=(self.panel_width, self.panel_height, 0.01),
            color=self.colors['background'],
            position=(0, 0, 0),
            parent=camera.ui,
            visible=False
        )
        
        self._create_layout()
        self._create_controls()
    
    def _create_layout(self):
        """Create the interface layout"""
        # Create sections
        self._create_header_section()
        self._create_inventory_section()
        self._create_equipment_section()
        self._create_stats_section()
        self._create_comparison_section()
    
    def _create_header_section(self):
        """Create header with title and mode buttons"""
        header_y = self.panel_height / 2 - 0.1
        
        # Title
        title = Text(
            'Inventory & Equipment',
            position=(0, header_y, 0.01),
            scale=2,
            color=self.colors['text'],
            parent=self.main_panel
        )
        self.ui_elements.append(title)
        
        # Mode buttons
        button_y = header_y - 0.08
        button_spacing = 0.15
        modes = [
            ('Inventory', InterfaceMode.INVENTORY),
            ('Equipment', InterfaceMode.EQUIPMENT),
            ('Compare', InterfaceMode.COMPARISON),
            ('Crafting', InterfaceMode.CRAFTING)
        ]
        
        for i, (label, mode) in enumerate(modes):
            x_pos = (i - len(modes) / 2 + 0.5) * button_spacing
            
            button = Button(
                text=label,
                position=(x_pos, button_y, 0.01),
                scale=0.08,
                color=self.colors['button'],
                text_color=self.colors['text'],
                parent=self.main_panel,
                on_click=lambda m=mode: self._set_mode(m)
            )
            self.ui_elements.append(button)
    
    def _create_inventory_section(self):
        """Create inventory grid"""
        grid_start_x = -self.panel_width / 2 + 0.1
        grid_start_y = self.panel_height / 2 - 0.25
        slot_size = 0.08
        slot_spacing = 0.09
        
        for y in range(self.grid_size[1]):
            row = []
            for x in range(self.grid_size[0]):
                slot_x = grid_start_x + x * slot_spacing
                slot_y = grid_start_y - y * slot_spacing
                
                slot = Entity(
                    model='cube',
                    scale=(slot_size, slot_size, 0.005),
                    color=self.colors['panel'],
                    position=(slot_x, slot_y, 0.005),
                    parent=self.main_panel
                )
                
                # Make slots interactive
                slot.on_click = lambda s=slot, pos=(x, y): self._on_inventory_slot_click(s, pos)
                
                row.append(slot)
                self.ui_elements.append(slot)
            
            self.inventory_grid.append(row)
    
    def _create_equipment_section(self):
        """Create equipment slots display"""
        equipment_x = self.panel_width / 2 - 0.2
        equipment_y = self.panel_height / 2 - 0.25
        
        # Equipment slots layout using EquipmentType
        slot_positions = {
            EquipmentType.WEAPON: (-0.15, 0),
            EquipmentType.ARMOR: (0, 0),
            EquipmentType.ACCESSORY: (0.15, 0),
            EquipmentType.CONSUMABLE: (0, -0.2)
        }
        
        slot_size = 0.1
        
        for slot_type, (offset_x, offset_y) in slot_positions.items():
            slot_x = equipment_x + offset_x
            slot_y = equipment_y + offset_y
            
            slot_entity = Entity(
                model='cube',
                scale=(slot_size, slot_size, 0.005),
                color=self.colors['panel'],
                position=(slot_x, slot_y, 0.005),
                parent=self.main_panel
            )
            
            # Add slot label
            label = Text(
                slot_type.value.replace('_', ' ').title(),
                position=(slot_x, slot_y - slot_size - 0.02, 0.01),
                scale=0.5,
                color=self.colors['text'],
                parent=self.main_panel
            )
            
            slot_entity.on_click = lambda s=slot_type: self._on_equipment_slot_click(s)
            
            self.equipment_slots[slot_type] = slot_entity
            self.ui_elements.extend([slot_entity, label])
    
    def _create_stats_section(self):
        """Create stats display section"""
        stats_x = -self.panel_width / 2 + 0.05
        stats_y = 0
        
        # Stats title
        stats_title = Text(
            'Character Stats',
            position=(stats_x, stats_y + 0.15, 0.01),
            scale=1.2,
            color=self.colors['text'],
            parent=self.main_panel
        )
        self.ui_elements.append(stats_title)
        
        # Create stat display entries
        stat_names = [
            'HP', 'MP', 'Physical Attack', 'Physical Defense',
            'Magical Attack', 'Magical Defense', 'Spiritual Attack', 'Spiritual Defense',
            'Movement Speed', 'Initiative'
        ]
        
        for i, stat_name in enumerate(stat_names):
            stat_y = stats_y + 0.08 - i * 0.04
            
            stat_text = Text(
                f'{stat_name}: 0',
                position=(stats_x, stat_y, 0.01),
                scale=0.8,
                color=self.colors['text'],
                parent=self.main_panel
            )
            
            self.stat_displays[stat_name] = stat_text
            self.ui_elements.append(stat_text)
    
    def _create_comparison_section(self):
        """Create equipment comparison section"""
        comparison_x = 0.2
        comparison_y = -0.1
        
        # Comparison title
        comparison_title = Text(
            'Equipment Comparison',
            position=(comparison_x, comparison_y + 0.15, 0.01),
            scale=1.2,
            color=self.colors['text'],
            parent=self.main_panel
        )
        self.ui_elements.append(comparison_title)
        
        # Comparison display area
        comparison_panel = Entity(
            model='cube',
            scale=(0.35, 0.25, 0.005),
            color=self.colors['panel'],
            position=(comparison_x, comparison_y, 0.005),
            parent=self.main_panel
        )
        self.ui_elements.append(comparison_panel)
    
    def _create_controls(self):
        """Create interface controls"""
        # Close button
        close_button = Button(
            text='X',
            position=(self.panel_width / 2 - 0.05, self.panel_height / 2 - 0.05, 0.01),
            scale=0.05,
            color=color.red,
            text_color=self.colors['text'],
            parent=self.main_panel,
            on_click=self.hide
        )
        self.ui_elements.append(close_button)
        
        # Action buttons
        button_y = -self.panel_height / 2 + 0.1
        button_spacing = 0.15
        
        action_buttons = [
            ('Equip', self._equip_selected_item),
            ('Unequip', self._unequip_selected_slot),
            ('Drop', self._drop_selected_item),
            ('Sort', self._sort_inventory)
        ]
        
        for i, (label, callback) in enumerate(action_buttons):
            x_pos = (i - len(action_buttons) / 2 + 0.5) * button_spacing
            
            button = Button(
                text=label,
                position=(x_pos, button_y, 0.01),
                scale=0.08,
                color=self.colors['button'],
                text_color=self.colors['text'],
                parent=self.main_panel,
                on_click=callback
            )
            self.ui_elements.append(button)
    
    def show(self, unit: GameEntity):
        """Show the inventory interface for a specific unit"""
        self.selected_unit = unit
        self.is_visible = True
        
        # Show UI elements
        self.modal_background.visible = True
        self.main_panel.visible = True
        
        # Update displays
        self._update_inventory_display()
        self._update_equipment_display()
        self._update_stats_display()
        
        # Disable game input
        camera.ui.enabled = True
    
    def hide(self):
        """Hide the inventory interface"""
        self.is_visible = False
        
        # Hide UI elements
        self.modal_background.visible = False
        self.main_panel.visible = False
        
        # Clear selections
        self.selected_item = None
        self.comparison_item = None
        
        # Re-enable game input
        camera.ui.enabled = False
    
    def _set_mode(self, mode: InterfaceMode):
        """Set the current interface mode"""
        self.current_mode = mode
        self._update_interface_for_mode()
    
    def _update_interface_for_mode(self):
        """Update interface elements based on current mode"""
        # This would show/hide different sections based on mode
        # For now, all sections are always visible
        pass
    
    def _on_inventory_slot_click(self, slot_entity: 'Entity', grid_pos: tuple):
        """Handle inventory slot click"""
        if not self.selected_unit:
            return
        
        # Get item at position (would need inventory system integration)
        item = self._get_item_at_position(grid_pos)
        
        if item:
            self._select_item(item)
            # Highlight selected slot
            slot_entity.color = self.colors['button_hover']
    
    def _on_equipment_slot_click(self, slot_type: EquipmentType):
        """Handle equipment slot click"""
        if not self.selected_unit:
            return
        
        # Get equipped item (would need equipment system integration)
        equipped_item = self._get_equipped_item(slot_type)
        
        if equipped_item:
            self._select_item(equipped_item)
            # Highlight selected slot
            self.equipment_slots[slot_type].color = self.colors['button_hover']
    
    def _select_item(self, item: EquipmentComponent):
        """Select an item for actions or comparison"""
        self.selected_item = item
        self._update_comparison_display()
    
    def _get_item_at_position(self, grid_pos: tuple) -> Optional[EquipmentComponent]:
        """Get item at inventory grid position"""
        # This would integrate with the actual inventory system
        # For now, return None as placeholder
        return None
    
    def _get_equipped_item(self, slot_type: EquipmentType) -> Optional[EquipmentComponent]:
        """Get currently equipped item in slot"""
        # This would integrate with the equipment system
        # For now, return None as placeholder
        return None
    
    def _update_inventory_display(self):
        """Update the inventory grid display"""
        if not self.selected_unit:
            return
        
        # This would populate the grid with actual inventory items
        # For now, just reset colors
        for row in self.inventory_grid:
            for slot in row:
                slot.color = self.colors['panel']
    
    def _update_equipment_display(self):
        """Update the equipment slots display"""
        if not self.selected_unit:
            return
        
        # Update each equipment slot
        for slot_type, slot_entity in self.equipment_slots.items():
            equipped_item = self._get_equipped_item(slot_type)
            
            if equipped_item:
                # Color by equipment tier
                tier_colors = {
                    EquipmentTier.BASE: self.colors['equipment_common'],
                    EquipmentTier.ENHANCED: self.colors['equipment_enhanced'],
                    EquipmentTier.ENCHANTED: self.colors['equipment_enchanted'],
                    EquipmentTier.SUPERPOWERED: self.colors['equipment_superpowered'],
                    EquipmentTier.METAPOWERED: self.colors['equipment_metapowered']
                }
                slot_entity.color = tier_colors.get(equipped_item.tier, self.colors['panel'])
            else:
                slot_entity.color = self.colors['panel']
    
    def _update_stats_display(self):
        """Update the character stats display"""
        if not self.selected_unit:
            return
        
        attributes = self.selected_unit.get_component(AttributeStats)
        if not attributes:
            return
        
        derived_stats = attributes.derived_stats
        
        # Update stat displays
        stat_mappings = {
            'HP': 'hp',
            'MP': 'mp',
            'Physical Attack': 'physical_attack',
            'Physical Defense': 'physical_defense',
            'Magical Attack': 'magical_attack',
            'Magical Defense': 'magical_defense',
            'Spiritual Attack': 'spiritual_attack',
            'Spiritual Defense': 'spiritual_defense',
            'Movement Speed': 'movement_speed',
            'Initiative': 'initiative'
        }
        
        for display_name, stat_key in stat_mappings.items():
            if display_name in self.stat_displays and stat_key in derived_stats:
                value = derived_stats[stat_key]
                self.stat_displays[display_name].text = f'{display_name}: {value}'
    
    def _update_comparison_display(self):
        """Update equipment comparison display"""
        if not self.selected_item or not self.selected_unit:
            return
        
        # Calculate stat changes if item were equipped
        stat_changes = self._calculate_stat_changes(self.selected_item)
        
        # Update comparison text (simplified for now)
        comparison_text = f"Selected: {self.selected_item.name}\n"
        comparison_text += f"Tier: {self.selected_item.tier.value}\n"
        
        for change in stat_changes:
            change_symbol = "+" if change.is_improvement else ""
            change_color = self.colors['stat_increase'] if change.is_improvement else self.colors['stat_decrease']
            comparison_text += f"{change.stat_name}: {change.old_value} → {change.new_value} ({change_symbol}{change.change})\n"
    
    def _calculate_stat_changes(self, item: EquipmentComponent) -> List[StatChange]:
        """Calculate what stat changes would occur if item were equipped"""
        if not self.selected_unit:
            return []
        
        # This would implement actual stat calculation logic
        # For now, return empty list as placeholder
        return []
    
    def _equip_selected_item(self):
        """Equip the currently selected item"""
        if not self.selected_item or not self.selected_unit:
            return
        
        # This would integrate with the equipment system
        print(f"Equipping {self.selected_item.name}")
        
        # Update displays
        self._update_equipment_display()
        self._update_stats_display()
    
    def _unequip_selected_slot(self):
        """Unequip item from selected equipment slot"""
        # This would integrate with the equipment system
        print("Unequipping selected item")
        
        # Update displays
        self._update_equipment_display()
        self._update_stats_display()
    
    def _drop_selected_item(self):
        """Drop the currently selected item"""
        if not self.selected_item:
            return
        
        # This would integrate with the inventory system
        print(f"Dropping {self.selected_item.name}")
        
        self.selected_item = None
        self._update_inventory_display()
    
    def _sort_inventory(self):
        """Sort inventory items"""
        # This would implement inventory sorting logic
        print("Sorting inventory")
        
        self._update_inventory_display()
    
    def update(self, delta_time: float):
        """Update interface animations and state"""
        if not self.is_visible:
            return
        
        # Handle input and animations here
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get interface statistics"""
        return {
            'is_visible': self.is_visible,
            'current_mode': self.current_mode.value,
            'selected_unit': self.selected_unit.id if self.selected_unit else None,
            'selected_item': self.selected_item.name if self.selected_item else None,
            'ui_elements_count': len(self.ui_elements)
        }
    
    def cleanup(self):
        """Clean up interface elements"""
        # Destroy all UI elements
        for element in self.ui_elements:
            if element and hasattr(element, 'destroy'):
                destroy(element)
        
        if self.modal_background:
            destroy(self.modal_background)
        
        if self.main_panel:
            destroy(self.main_panel)
        
        # Clear references
        self.ui_elements.clear()
        self.inventory_grid.clear()
        self.equipment_slots.clear()
        self.stat_displays.clear()
        self.comparison_displays.clear()