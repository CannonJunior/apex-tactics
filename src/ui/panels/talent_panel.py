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
        
        # Load icon scale from master UI config
        from src.core.ui.ui_config_manager import get_ui_config_manager
        ui_config = get_ui_config_manager()
        icon_scale = ui_config.get('panels.talent_panel.talent_grid.icon_scale', 0.06)
        
        # Create icon entity
        super().__init__(
            parent=parent,
            model='cube',
            texture='white_cube',
            color=self._get_talent_color(),
            scale=icon_scale,
            **kwargs
        )
        
        # Create tooltip using master UI config
        from src.core.ui.ui_config_manager import get_ui_config_manager
        ui_config = get_ui_config_manager()
        
        tooltip_text = f"{talent_data['name']}\n{talent_data['description']}\nAction: {talent_data.get('action_type', 'Unknown')}"
        self.tooltip = Tooltip(tooltip_text)
        tooltip_bg_color = ui_config.get_color('panels.talent_panel.tooltip.background_color', '#000000CC')
        self.tooltip.background.color = tooltip_bg_color
        
        # Store original position for drag operations (like inventory items)
        self.org_pos = None
    
    def _get_icon_scale(self):
        """Get icon scale from master UI config."""
        from src.core.ui.ui_config_manager import get_ui_config_manager
        ui_config = get_ui_config_manager()
        return ui_config.get('panels.talent_panel.talent_grid.icon_scale', 0.06)
        
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
        from src.core.ui.ui_config_manager import get_ui_config_manager
        ui_config = get_ui_config_manager()
        
        self.org_pos = (self.x, self.y)
        drag_z_offset = ui_config.get('panels.talent_panel.visual_effects.drag_z_offset', 0.01)
        self.z -= drag_z_offset  # Move talent forward visually
        
        # Disable camera movement during drag
        self._set_camera_drag_state(True, "talent icon")
        
        print(f"Dragging {self.talent_data['name']}")
    
    def drop(self):
        """Called when talent is dropped."""
        from src.core.ui.ui_config_manager import get_ui_config_manager
        ui_config = get_ui_config_manager()
        
        self.x = round(self.x, 3)
        self.y = round(self.y, 3)
        drop_z_offset = ui_config.get('panels.talent_panel.visual_effects.drag_z_offset', 0.01)
        self.z += drop_z_offset  # Move talent back
        
        # Re-enable camera movement after drag
        self._set_camera_drag_state(False, "talent icon")
        
        # Check if dropped on valid hotkey slot
        dropped_on_slot, target_slot = self._check_hotkey_slot_drop()
        
        print(f"Dropping talent {self.talent_data['name']} at ({self.x:.3f}, {self.y:.3f})")
        
        if dropped_on_slot is not None:
            # Valid drop - snap to the hotkey slot position first
            self._snap_to_slot_position(target_slot)
            
            # Enhanced logging for talent drop
            print(f"🎮 TALENT DROP SUCCESS: '{self.talent_data['name']}' dropped onto HOTKEY SLOT #{dropped_on_slot + 1}")
            print(f"   📍 Drop coordinates: ({self.x:.3f}, {self.y:.3f})")
            print(f"   🎯 Target slot position: ({target_slot.x:.3f}, {target_slot.y:.3f})")
            print(f"   🆔 Slot index (0-based): {dropped_on_slot}")
            print(f"   🎨 Talent type: {self.talent_data.get('action_type', 'Unknown')}")
            
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
            print(f"❌ INVALID DROP: '{self.talent_data['name']}' not dropped on any hotkey slot")
            print(f"   📍 Drop position: ({self.x:.3f}, {self.y:.3f})")
            print(f"   🔄 Returning talent to original position")
            self.position = self.org_pos
    
    def _check_hotkey_slot_drop(self):
        """Check if dropped on a valid hotkey slot. Returns (slot_index, slot_object) or (None, None)."""
        # Get reference to tactical RPG controller with hotkey slots
        if hasattr(self.talent_panel, 'game_reference') and self.talent_panel.game_reference:
            tactical_controller = self.talent_panel.game_reference
            
            # FIXED: Check direct hotkey_slots first (this is the correct path)
            if hasattr(tactical_controller, 'hotkey_slots') and tactical_controller.hotkey_slots:
                # DEBUG: Print all hotkey slot positions for analysis
                print(f"🔍 DEBUG: Checking {len(tactical_controller.hotkey_slots)} hotkey slots for drop at ({self.x:.3f}, {self.y:.3f})")
                for debug_i, debug_slot in enumerate(tactical_controller.hotkey_slots):
                    debug_x = getattr(debug_slot, 'x', 0)
                    debug_y = getattr(debug_slot, 'y', 0)
                    debug_dist = ((self.x - debug_x)**2 + (self.y - debug_y)**2)**0.5
                    print(f"   Slot #{debug_i + 1}: pos({debug_x:.3f}, {debug_y:.3f}) dist={debug_dist:.3f}")
                
                # FIXED: Find the CLOSEST slot instead of first slot within threshold
                closest_slot = None
                closest_distance = float('inf')
                closest_index = -1
                
                for i, slot in enumerate(tactical_controller.hotkey_slots):
                    # Use slot position directly
                    slot_x = getattr(slot, 'x', 0)
                    slot_y = getattr(slot, 'y', 0)
                    
                    # Calculate distance
                    distance = ((self.x - slot_x)**2 + (self.y - slot_y)**2)**0.5
                    
                    # Track the closest slot
                    if distance < closest_distance:
                        closest_distance = distance
                        closest_slot = slot
                        closest_index = i
                
                # Check if closest slot is within threshold
                from src.core.ui.ui_config_manager import get_ui_config_manager
                ui_config = get_ui_config_manager()
                drop_threshold = ui_config.get('panels.talent_panel.talent_grid.drag_drop_threshold', 0.12)
                
                if closest_distance < drop_threshold:
                    print(f"🎯 HOTKEY SLOT DETECTION: Mouse over HOTKEY #{closest_index + 1}")
                    print(f"   📏 Distance from slot center: {closest_distance:.3f} (threshold: 0.12)")
                    print(f"   📍 Talent drop position: ({self.x:.3f}, {self.y:.3f})")
                    print(f"   📌 Hotkey slot position: ({closest_slot.x:.3f}, {closest_slot.y:.3f})")
                    print(f"   🔢 Slot index (0-based): {closest_index}")
                    print(f"   ✅ Valid drop zone detected - USING CLOSEST SLOT LOGIC")
                    return closest_index, closest_slot
            # Fallback: check if controller has ui_manager.hotkey_slots (unlikely)
            elif hasattr(tactical_controller, 'ui_manager') and hasattr(tactical_controller.ui_manager, 'hotkey_slots'):
                for i, slot in enumerate(tactical_controller.ui_manager.hotkey_slots):
                    slot_x = getattr(slot, 'x', 0)
                    slot_y = getattr(slot, 'y', 0)
                    
                    distance = ((self.x - slot_x)**2 + (self.y - slot_y)**2)**0.5
                    if distance < 0.12:
                        print(f"🎯 Dropped near hotkey slot {i + 1} (distance: {distance:.3f}) [ui_manager path]")
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
    
    def _set_camera_drag_state(self, is_dragging: bool, source: str):
        """Set camera drag state through game reference."""
        try:
            # Access camera controller through talent panel's game reference
            if (hasattr(self.talent_panel, 'game_reference') and
                hasattr(self.talent_panel.game_reference, 'camera_controller')):
                camera_controller = self.talent_panel.game_reference.camera_controller
                camera_controller.set_ui_dragging(is_dragging, source)
            else:
                print(f"⚠️ Could not access camera controller for {source} drag state")
        except Exception as e:
            print(f"⚠️ Error setting camera drag state: {e}")
    
    
    def _place_talent_in_slot(self, slot_index: int):
        """Place this talent in the specified hotkey slot."""
        if not self.talent_panel.game_reference:
            return
            
        tactical_controller = self.talent_panel.game_reference
        
        # FIXED: Get hotkey slots from direct reference first
        hotkey_slots = None
        if hasattr(tactical_controller, 'hotkey_slots') and tactical_controller.hotkey_slots:
            hotkey_slots = tactical_controller.hotkey_slots
            print(f"🔗 Using direct hotkey_slots (correct path)")
        elif hasattr(tactical_controller, 'ui_manager') and hasattr(tactical_controller.ui_manager, 'hotkey_slots'):
            hotkey_slots = tactical_controller.ui_manager.hotkey_slots
            print(f"🔗 Using ui_manager.hotkey_slots (fallback path)")
            
        if not hotkey_slots:
            print("❌ No hotkey slots found")
            return
            
        if slot_index >= len(hotkey_slots):
            print(f"❌ Invalid slot index {slot_index}")
            return
            
        target_slot = hotkey_slots[slot_index]
        
        print(f"📋 HOTKEY ASSIGNMENT: Assigning '{self.talent_data['name']}' to HOTKEY #{slot_index + 1}")
        print(f"   🎯 Target hotkey slot: #{slot_index + 1} (0-based index: {slot_index})")
        print(f"   📌 Slot position: ({getattr(target_slot, 'x', 'unknown')}, {getattr(target_slot, 'y', 'unknown')})")
        print(f"   🎨 Talent type: {self.talent_data.get('action_type', 'Unknown')}")
        print(f"   🆔 Talent ID: {self.talent_data.get('id', 'unknown')}")
        
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
        
        # Get icon scale from master UI config
        from src.core.ui.ui_config_manager import get_ui_config_manager
        ui_config = get_ui_config_manager()
        icon_scale = ui_config.get('panels.talent_panel.talent_grid.icon_scale', 0.06)
        slot_scale_factor = ui_config.get('panels.talent_panel.talent_grid.slot_scale_factor', 0.8)
        
        # Create new talent icon in the slot using master UI config
        slot_icon_z_offset = ui_config.get('panels.talent_panel.visual_effects.slot_icon_z_offset', -0.01)
        
        slot_icon = Entity(
            parent=target_slot,
            model='cube',
            texture='white_cube',
            color=self._get_talent_color(),
            scale=icon_scale * slot_scale_factor,
            position=(0, 0, slot_icon_z_offset)
        )
        
        # Store talent data on the slot icon for reference
        slot_icon.talent_data = self.talent_data
        
        # Create tooltip for slot icon using master UI config
        tooltip_text = f"{self.talent_data['name']}\n{self.talent_data['description']}\nAction: {self.talent_data.get('action_type', 'Unknown')}\nHotkey: {slot_index + 1}"
        slot_icon.tooltip = Tooltip(tooltip_text)
        tooltip_bg_color = ui_config.get_color('panels.talent_panel.tooltip.background_color', '#000000')
        tooltip_alpha = ui_config.get('panels.talent_panel.tooltip.background_alpha', 0.8)
        slot_icon.tooltip.background.color = color.rgba(*tooltip_bg_color, tooltip_alpha)
        
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
        
        # Get tab configuration from master UI config
        from src.core.ui.ui_config_manager import get_ui_config_manager
        ui_config = get_ui_config_manager()
        
        tab_config = ui_config.get('panels.talent_panel.tabs', {})
        button_spacing = tab_config.get('button_spacing', 0.3)
        button_offset = tab_config.get('button_offset', -0.3)
        y_position = tab_config.get('y_position', 0.35)
        scale = tab_config.get('scale', {'x': 0.2, 'y': 0.4})
        active_color = ui_config.get_color('panels.talent_panel.tabs.colors.active', '#87CEEB')
        inactive_color = ui_config.get_color('panels.talent_panel.tabs.colors.inactive', '#696969')
        
        for i, tab in enumerate(tabs):
            x_offset = i * button_spacing + button_offset
            
            btn = Button(
                text=tab,
                parent=self.panel,  # Attach to panel so they move together
                color=active_color if tab == self.current_tab else inactive_color,
                scale=(scale['x'], scale['y']),
                # Position relative to panel
                position=(x_offset, y_position, 0),
                on_click=lambda t=tab: self.switch_tab(t)
            )
            
            # Debug output to verify positioning
            print(f"🏷️ Created tab '{tab}' at panel-relative position ({x_offset:.2f}, {y_position:.2f}, 0)")
            
            # Start hidden to match panel visibility
            btn.enabled = False
            self.tab_buttons.append(btn)
    
    def _position_panel(self):
        """Position the panel using master UI config."""
        from src.core.ui.ui_config_manager import get_ui_config_manager
        ui_config = get_ui_config_manager()
        
        if self.panel:
            panel_position = ui_config.get_position('panels.talent_panel.main_panel.position')
            self.panel.x = panel_position['x']
            self.panel.y = panel_position['y']
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
        
        # Get talent grid configuration from master UI config
        from src.core.ui.ui_config_manager import get_ui_config_manager
        ui_config = get_ui_config_manager()
        
        grid_config = ui_config.get('panels.talent_panel.talent_grid', {})
        start_position = grid_config.get('start_position', {'x': 0.05, 'y': -0.15})
        icons_per_row = grid_config.get('icons_per_row', 3)
        spacing = grid_config.get('spacing', {'x': 0.1, 'y': 0.08})
        max_talents = grid_config.get('max_talents', 12)
        
        # Position icons below the panel
        start_x = panel_x + start_position['x']
        start_y = panel_y + start_position['y']
        max_per_row = icons_per_row
        
        for i, talent in enumerate(current_talents[:max_talents]):
            row = i // max_per_row
            col = i % max_per_row
            
            x = start_x + col * spacing['x']
            y = start_y - row * spacing['y']
            
            # Create draggable talent icon
            talent_icon = DraggableTalentIcon(
                talent,
                self,
                position=(x, y, 0)
            )
            self.talent_icons.append(talent_icon)
        
        # Update tab button colors using master UI config
        from src.core.ui.ui_config_manager import get_ui_config_manager
        ui_config = get_ui_config_manager()
        
        tab_names = ui_config.get('panels.talent_panel.tabs.names', ["Physical", "Magical", "Spiritual"])
        active_color = ui_config.get_color('panels.talent_panel.tabs.colors.active', '#87CEEB')
        inactive_color = ui_config.get_color('panels.talent_panel.tabs.colors.inactive', '#696969')
        
        for i, btn in enumerate(self.tab_buttons):
            if i < len(tab_names):
                tab_name = tab_names[i]
                btn.color = active_color if tab_name == self.current_tab else inactive_color
    
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
                
                print(f"🔗 Character data assignment:")
                print(f"   slot_index (0-based): {slot_index}")
                print(f"   slot_key (1-based): {slot_key}")
                print(f"   talent_id: {talent_id}")
                
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
            
            # Tabs are children of panel and should inherit visibility automatically,
            # but explicitly enable/disable them to ensure proper behavior
            for btn in self.tab_buttons:
                btn.enabled = self.panel.enabled
            
            # Update display to show/hide talent icons
            if self.panel.enabled:
                self._update_display()
            else:
                self._clear_talent_icons()
                
            status = "shown" if self.panel.enabled else "hidden"
            print(f"Talent panel {status} (tabs attached as children)")
    
    def show(self):
        """Show the talent panel."""
        if self.panel:
            self.panel.enabled = True
            # Ensure tabs are enabled when panel is shown
            for btn in self.tab_buttons:
                btn.enabled = True
            self._update_display()
    
    def hide(self):
        """Hide the talent panel."""
        if self.panel:
            self.panel.enabled = False
            # Explicitly disable tabs when panel is hidden
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
