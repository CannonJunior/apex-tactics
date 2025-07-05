"""
Talent Panel Implementation

Displays talent trees with physical, magical, and spiritual ability trees.
Shows available abilities for assignment in the selected unit.
Features draggable talent icons that can be dropped to hotkey slots.
Toggleable with 't' key.
"""

from typing import Optional, Dict, Any, List
import traceback

try:
    from ursina import Entity, Text, Button, color, camera, destroy, Draggable, mouse
    from ursina.prefabs.window_panel import WindowPanel
    from ursina.prefabs.tooltip import Tooltip
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False


class DraggableTalentIcon(Draggable):
    """Draggable talent icon that can be assigned to hotkey slots."""
    
    def __init__(self, talent_data: Dict[str, Any], talent_panel, **kwargs):
        if not URSINA_AVAILABLE:
            return
            
        self.talent_data = talent_data
        self.talent_panel = talent_panel
        
        # Handle parent parameter properly
        parent = kwargs.pop('parent', camera.ui)
        
        # Load icon scale from UI config
        icon_scale = self._get_icon_scale()
        
        # Create icon entity
        super().__init__(
            parent=parent,
            model='cube',
            texture='white_cube',
            color=self._get_talent_color(),
            scale=icon_scale,
            **kwargs
        )
        
        # Create tooltip
        tooltip_text = f"{talent_data['name']}\n{talent_data['description']}\nAction: {talent_data.get('action_type', 'Unknown')}"
        self.tooltip = Tooltip(tooltip_text)
        self.tooltip.background.color = color.hsv(0, 0, 0, .8)
        
        # Store original position for drag operations (like inventory items)
        self.org_pos = None
    
    def _get_icon_scale(self):
        """Get icon scale from unified action item configuration."""
        try:
            from src.core.assets.data_manager import get_action_item_scale
            scale = get_action_item_scale()
            print(f"🎨 Loaded talent icon scale: {scale}")
            return scale
        except Exception as e:
            print(f"⚠️ Could not load icon scale: {e}, using fallback")
            return 0.06  # Default scale to match hotkeys
        
    def _get_talent_color(self):
        """Get color based on talent action type using unified configuration."""
        action_type = self.talent_data.get('action_type', 'Attack')
        
        try:
            from src.core.assets.data_manager import get_action_item_color, convert_hex_to_ursina_color
            color_hex = get_action_item_color(action_type)
            ursina_color = convert_hex_to_ursina_color(color_hex)
            print(f"🎨 Loaded {action_type} color: {color_hex}")
            return ursina_color
        except Exception as e:
            print(f"⚠️ Could not load unified colors: {e}, using fallback")
            
            # Fallback color map
            color_map = {
                'Attack': color.red,
                'Magic': color.blue, 
                'Spirit': color.yellow,
                'Move': color.green,
                'Inventory': color.orange
            }
            return color_map.get(action_type, color.white)
    
    def drag(self):
        """Called when talent starts being dragged."""
        self.org_pos = (self.x, self.y)
        self.z -= .01  # Move talent forward visually
        print(f"Dragging {self.talent_data['name']}")
    
    def drop(self):
        """Called when talent is dropped."""
        self.x = round(self.x, 3)
        self.y = round(self.y, 3)
        self.z += .01  # Move talent back
        
        # Check if dropped on valid hotkey slot
        dropped_on_slot, target_slot = self._check_hotkey_slot_drop()
        
        print(f"Dropping talent {self.talent_data['name']} at ({self.x:.3f}, {self.y:.3f})")
        
        if dropped_on_slot is not None:
            # Valid drop - snap to the hotkey slot position first
            self._snap_to_slot_position(target_slot)
            
            # Let the user see the snap for a brief moment
            print(f"✅ Valid drop on hotkey slot {dropped_on_slot + 1} - snapped to position")
            
            # Then place talent in hotkey slot
            self._place_talent_in_slot(dropped_on_slot)
            
            # Return talent icon to original position after a brief delay
            # Import and use invoke for a delayed return
            try:
                from ursina import invoke
                invoke(self._return_to_original_position, delay=0.3)  # 0.3 second delay
            except ImportError:
                # Fallback: immediate return if invoke not available
                self.position = self.org_pos
        else:
            # Invalid drop location - return to original position immediately
            print(f"❌ Invalid drop location for {self.talent_data['name']} - returning to original position")
            self.position = self.org_pos
    
    def _check_hotkey_slot_drop(self):
        """Check if dropped on a valid hotkey slot. Returns (slot_index, slot_object) or (None, None)."""
        # Get reference to tactical RPG controller with hotkey slots
        if hasattr(self.talent_panel, 'game_reference') and self.talent_panel.game_reference:
            tactical_controller = self.talent_panel.game_reference
            
            # Access hotkey slots through UI manager
            if hasattr(tactical_controller, 'ui_manager') and hasattr(tactical_controller.ui_manager, 'hotkey_slots'):
                # Check each hotkey slot for proximity
                for i, slot in enumerate(tactical_controller.ui_manager.hotkey_slots):
                    # Use slot position directly
                    slot_x = getattr(slot, 'x', 0)
                    slot_y = getattr(slot, 'y', 0)
                    
                    # Calculate distance with generous threshold for easier dropping
                    distance = ((self.x - slot_x)**2 + (self.y - slot_y)**2)**0.5
                    if distance < 0.12:  # Generous drop zone
                        print(f"🎯 Dropped near hotkey slot {i + 1} (distance: {distance:.3f})")
                        return i, slot
            # Fallback: check if controller has direct hotkey_slots attribute (legacy compatibility)
            elif hasattr(tactical_controller, 'hotkey_slots'):
                for i, slot in enumerate(tactical_controller.hotkey_slots):
                    slot_x = getattr(slot, 'x', 0)
                    slot_y = getattr(slot, 'y', 0)
                    
                    distance = ((self.x - slot_x)**2 + (self.y - slot_y)**2)**0.5
                    if distance < 0.12:
                        print(f"🎯 Dropped near hotkey slot {i + 1} (distance: {distance:.3f}) [legacy path]")
                        return i, slot
        
        print(f"📍 Dropped at position ({self.x:.3f}, {self.y:.3f}) - no valid hotkey slot nearby")
        return None, None
    
    def _snap_to_slot_position(self, target_slot):
        """Snap the talent icon to the exact position of the target hotkey slot."""
        if target_slot:
            # Snap to the exact slot position (similar to inventory grid snapping)
            self.x = round(target_slot.x, 3)
            self.y = round(target_slot.y, 3)
            print(f"📌 Snapped talent icon to slot position ({self.x:.3f}, {self.y:.3f})")
    
    def _return_to_original_position(self):
        """Return the talent icon to its original position."""
        if hasattr(self, 'org_pos') and self.org_pos:
            self.position = self.org_pos
            print(f"🔄 Returned {self.talent_data['name']} to original position")
    
    
    def _place_talent_in_slot(self, slot_index: int):
        """Place this talent in the specified hotkey slot."""
        if not self.talent_panel.game_reference:
            return
            
        tactical_controller = self.talent_panel.game_reference
        
        # Get hotkey slots from UI manager or direct reference
        hotkey_slots = None
        if hasattr(tactical_controller, 'ui_manager') and hasattr(tactical_controller.ui_manager, 'hotkey_slots'):
            hotkey_slots = tactical_controller.ui_manager.hotkey_slots
        elif hasattr(tactical_controller, 'hotkey_slots'):
            hotkey_slots = tactical_controller.hotkey_slots
            
        if not hotkey_slots:
            print("❌ No hotkey slots found")
            return
            
        if slot_index >= len(hotkey_slots):
            print(f"❌ Invalid slot index {slot_index}")
            return
            
        target_slot = hotkey_slots[slot_index]
        
        # Remove any existing talent icons in this slot (fix the cleanup issue)
        children_to_remove = []
        for child in target_slot.children:
            # Check if this is a talent icon (has talent_data or is not the slot itself)
            if (hasattr(child, 'talent_data') or 
                (hasattr(child, 'model') and child != target_slot)):
                children_to_remove.append(child)
        
        for child in children_to_remove:
            print(f"Removing existing icon from slot {slot_index + 1}: {type(child)}")
            if hasattr(child, 'tooltip') and child.tooltip:
                destroy(child.tooltip)
            destroy(child)
        
        # Get icon scale from unified action item config
        try:
            from src.core.assets.data_manager import get_action_item_scale
            icon_scale = get_action_item_scale()
            print(f"🎨 Using unified icon scale for hotkey slot: {icon_scale}")
        except Exception as e:
            print(f"⚠️ Could not load unified icon scale: {e}")
            icon_scale = 0.06
        
        # Create new talent icon in the slot
        slot_icon = Entity(
            parent=target_slot,
            model='cube',
            texture='white_cube',
            color=self._get_talent_color(),
            scale=icon_scale * 0.8,  # Slightly smaller than configured scale
            position=(0, 0, -0.01)  # Slightly in front of slot
        )
        
        # Store talent data on the slot icon for reference
        slot_icon.talent_data = self.talent_data
        
        # Create tooltip for slot icon
        tooltip_text = f"{self.talent_data['name']}\n{self.talent_data['description']}\nAction: {self.talent_data.get('action_type', 'Unknown')}\nHotkey: {slot_index + 1}"
        slot_icon.tooltip = Tooltip(tooltip_text)
        slot_icon.tooltip.background.color = color.hsv(0, 0, 0, .8)
        
        # Update character's hotkey abilities
        self.talent_panel._assign_talent_to_hotkey(self.talent_data, slot_index)
        
        print(f"✅ Placed {self.talent_data['name']} in hotkey slot {slot_index + 1}")


class TalentPanel:
    """
    Talent tree panel showing abilities available for assignment.
    
    Features:
    - 3 tabs for physical, magical, and spiritual talents
    - Tree structure with low level abilities at top
    - Draggable talent icons that can be assigned to hotkey slots
    - Loads all talents from asset data files
    """
    
    def __init__(self, game_reference: Optional[Any] = None):
        """Initialize talent panel."""
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for TalentPanel")
        
        self.game_reference = game_reference
        self.current_character = None
        self.current_tab = "Physical"
        self.talent_trees: Dict[str, List[Dict[str, Any]]] = {}
        self.talent_icons: List[DraggableTalentIcon] = []
        
        # UI elements
        self.panel = None
        self.tab_buttons = []
        
        # Load talent data from assets
        self._load_talents_from_assets()
        
        # Create UI elements
        self._create_ui_elements()
        
        # Position panel
        self._position_panel()
        
        # Don't update display initially since panel starts hidden
    
    def _load_talents_from_assets(self):
        """Load talent data from asset files using data manager."""
        try:
            from src.core.assets.data_manager import get_data_manager
            data_manager = get_data_manager()
            
            # Get all talents
            all_talents = data_manager.get_all_talents()
            
            # Organize by action type to tree mapping
            tree_mapping = {
                'Attack': 'Physical',
                'Magic': 'Magical', 
                'Spirit': 'Spiritual',
                'Move': 'Physical',  # Movement abilities go in Physical tree
                'Inventory': 'Physical'  # Inventory abilities go in Physical tree
            }
            
            # Initialize trees
            for tree_name in ['Physical', 'Magical', 'Spiritual']:
                self.talent_trees[tree_name] = []
            
            # Organize talents into trees
            for talent in all_talents:
                action_type = talent.action_type
                tree_name = tree_mapping.get(action_type, 'Physical')
                
                # Convert TalentData to dict for UI
                talent_dict = {
                    'id': talent.id,
                    'name': talent.name,
                    'level': talent.level,
                    'tier': talent.tier,
                    'description': talent.description,
                    'action_type': talent.action_type,
                    'requirements': talent.requirements,
                    'effects': talent.effects,
                    'cost': talent.cost,
                    'learned': False  # Default to not learned
                }
                
                self.talent_trees[tree_name].append(talent_dict)
            
            # Sort talents by level within each tree
            for tree_name in self.talent_trees:
                self.talent_trees[tree_name].sort(key=lambda t: t['level'])
            
            print(f"✅ Loaded talents from assets:")
            for tree_name, talents in self.talent_trees.items():
                print(f"  {tree_name}: {len(talents)} talents")
                
        except Exception as e:
            print(f"❌ Error loading talents from assets: {e}")
            traceback.print_exc()
            self._load_fallback_talents()
    
    def _load_fallback_talents(self):
        """Load minimal fallback talent data if assets fail."""
        self.talent_trees = {
            "Physical": [
                {"id": "basic_strike", "name": "Basic Strike", "level": 1, "tier": "Novice", "learned": False, "description": "Basic melee attack", "action_type": "Attack"},
                {"id": "power_attack", "name": "Power Attack", "level": 2, "tier": "Novice", "learned": False, "description": "Stronger attack", "action_type": "Attack"},
            ],
            "Magical": [
                {"id": "magic_missile", "name": "Magic Missile", "level": 1, "tier": "Novice", "learned": False, "description": "Basic spell", "action_type": "Magic"},
                {"id": "heal", "name": "Heal", "level": 2, "tier": "Novice", "learned": False, "description": "Restore health", "action_type": "Magic"},
            ],
            "Spiritual": [
                {"id": "inner_peace", "name": "Inner Peace", "level": 1, "tier": "Novice", "learned": False, "description": "Restore energy", "action_type": "Spirit"},
                {"id": "blessing", "name": "Blessing", "level": 2, "tier": "Novice", "learned": False, "description": "Stat boost", "action_type": "Spirit"},
            ],
        }
        print("⚠️ Using fallback talent data")
    
    def _create_ui_elements(self):
        """Create all UI elements."""
        # Create content texts for the panel
        self.title_text = Text('Talent Trees')
        self.current_tab_text = Text(f'Current Tab: {self.current_tab}')
        self.instruction_text = Text('Drag talents to hotkey slots to assign')
        
        # Create main panel with content
        self.panel = WindowPanel(
            title='Talent Trees',
            content=(
                self.title_text,
                self.current_tab_text,
                Text(''),  # Spacer
                self.instruction_text,
                Text(''),  # Spacer
                Text('Talent Icons will appear below the panel')
            ),
            popup=False
        )
        
        # Start hidden
        self.panel.enabled = False
        
        # Create tab buttons
        self._create_tab_buttons()
    
    def _create_tab_buttons(self):
        """Create tab buttons for switching between talent trees."""
        tabs = ["Physical", "Magical", "Spiritual"]
        
        for i, tab in enumerate(tabs):
            btn = Button(
                text=tab,
                parent=camera.ui,
                color=color.azure if tab == self.current_tab else color.dark_gray,
                scale=(0.08, 0.03),
                position=(0.25 + i * 0.09, 0.4),
                on_click=lambda t=tab: self.switch_tab(t)
            )
            self.tab_buttons.append(btn)
    
    def _position_panel(self):
        """Position the panel on the right side of the screen."""
        if self.panel:
            self.panel.x = 0.25
            self.panel.y = 0.0
            self.panel.layout()
    
    def _update_display(self):
        """Update the display with current talent tree."""
        # Update panel text content
        if hasattr(self, 'current_tab_text'):
            self.current_tab_text.text = f'Current Tab: {self.current_tab}'
        
        # Clear existing talent icons
        self._clear_talent_icons()
        
        # Only create icons if panel is visible
        if not self.panel or not self.panel.enabled:
            return
        
        # Get current tab talents
        current_talents = self.talent_trees.get(self.current_tab, [])
        
        # Create talent icons positioned relative to panel
        panel_x = self.panel.x if self.panel else 0.25
        panel_y = self.panel.y if self.panel else 0.0
        
        # Position icons below the panel
        start_x = panel_x + 0.05
        start_y = panel_y - 0.15  # Below the panel
        max_per_row = 3
        
        for i, talent in enumerate(current_talents[:12]):  # Show up to 12 talents
            row = i // max_per_row
            col = i % max_per_row
            
            x = start_x + col * 0.1
            y = start_y - row * 0.08
            
            # Create draggable talent icon
            talent_icon = DraggableTalentIcon(
                talent,
                self,
                position=(x, y, 0)
            )
            self.talent_icons.append(talent_icon)
        
        # Update tab button colors
        for i, btn in enumerate(self.tab_buttons):
            tab_name = ["Physical", "Magical", "Spiritual"][i]
            btn.color = color.azure if tab_name == self.current_tab else color.dark_gray
    
    def _clear_talent_icons(self):
        """Clear all existing talent icons."""
        for icon in self.talent_icons:
            if hasattr(icon, 'tooltip') and icon.tooltip:
                destroy(icon.tooltip)
            destroy(icon)
        self.talent_icons.clear()
    
    def switch_tab(self, tab_name: str):
        """Switch to different talent tree tab."""
        valid_tabs = ["Physical", "Magical", "Spiritual"]
        if tab_name in valid_tabs:
            self.current_tab = tab_name
            self._update_display()
            print(f"Switched to {tab_name} talents")
    
    def _assign_talent_to_hotkey(self, talent_data: Dict[str, Any], slot_index: int):
        """
        Assign a talent to a hotkey slot by updating character data.
        
        Args:
            talent_data: Dictionary containing talent information including 'id'
            slot_index: 0-based index of the hotkey slot to assign to
        """
        if not self.game_reference:
            print("❌ No game reference available")
            return
            
        # Get character state manager
        if hasattr(self.game_reference, 'character_state_manager'):
            char_manager = self.game_reference.character_state_manager
            active_character = char_manager.get_active_character()
            
            if active_character:
                # Update character's hotkey abilities
                if not hasattr(active_character, 'template_data'):
                    print("❌ Character missing template_data")
                    return
                    
                if 'hotkey_abilities' not in active_character.template_data:
                    active_character.template_data['hotkey_abilities'] = {}
                
                # Assign talent to slot
                slot_key = str(slot_index + 1)
                talent_id = talent_data['id']
                
                # Update character's hotkey abilities data
                active_character.template_data['hotkey_abilities'][slot_key] = {
                    'talent_id': talent_id
                }
                
                print(f"📝 Updated character data: slot {slot_key} -> talent_id '{talent_id}'")
                
                # Notify character state manager of changes to trigger updates
                if hasattr(char_manager, '_notify_observers'):
                    char_manager._notify_observers('character_updated', active_character.instance_id, active_character)
                
                # Update hotkey slots display to refresh colors and tooltips
                if hasattr(self.game_reference, 'update_hotkey_slots'):
                    self.game_reference.update_hotkey_slots()
                    
                # Update character panel if it exists
                if hasattr(self.game_reference, 'control_panel') and self.game_reference.control_panel:
                    self.game_reference.control_panel.update_unit_info(self.game_reference.active_unit)
                
                print(f"✅ Assigned talent '{talent_data['name']}' to hotkey slot {slot_index + 1}")
                print(f"🔄 Character state updated and observers notified")
            else:
                print("❌ No active character selected")
        else:
            print("❌ No character state manager available")
    
    
    def set_character(self, character):
        """
        Set the character to display talents for.
        
        Args:
            character: Character object to display, or None to clear
        """
        self.current_character = character
        # Could update learned status based on character data
        print(f"Set character for talent panel: {getattr(character, 'name', 'None')}")
    
    def toggle_visibility(self):
        """Toggle the visibility of the talent panel."""
        if self.panel:
            self.panel.enabled = not self.panel.enabled
            
            # Also toggle tab buttons
            for btn in self.tab_buttons:
                btn.enabled = self.panel.enabled
            
            # Update display to show/hide talent icons
            if self.panel.enabled:
                self._update_display()
            else:
                self._clear_talent_icons()
                
            status = "shown" if self.panel.enabled else "hidden"
            print(f"Talent panel {status}")
    
    def show(self):
        """Show the talent panel."""
        if self.panel:
            self.panel.enabled = True
            for btn in self.tab_buttons:
                btn.enabled = True
            self._update_display()
    
    def hide(self):
        """Hide the talent panel."""
        if self.panel:
            self.panel.enabled = False
            for btn in self.tab_buttons:
                btn.enabled = False
            self._clear_talent_icons()
    
    def is_visible(self) -> bool:
        """Check if the talent panel is currently visible."""
        if self.panel:
            return self.panel.enabled
        return False
    
    def cleanup(self):
        """Clean up panel resources."""
        self._clear_talent_icons()
        
        for btn in self.tab_buttons:
            destroy(btn)
        self.tab_buttons.clear()
        
        if self.panel:
            self.panel.enabled = False
            destroy(self.panel)