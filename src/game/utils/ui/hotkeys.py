"""
Hotkeys

"""

from typing import Any, Dict, List, Optional, Set

try:
    from ursina import Entity, color, destroy, Button, Text, WindowPanel, camera, Tooltip
    from ursina.prefabs.health_bar import HealthBar, Tooltip
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False

def hotkey_update_hotkey_slot_ability_data(self, slot_index: int, ability_data: Dict[str, Any]):
    """Update the ability_data for a specific hotkey slot."""
    if not hasattr(self, 'hotkey_slots') or not self.hotkey_slots:
        print(f"❌ No hotkey slots available")
        return False

    if slot_index < 0 or slot_index >= len(self.hotkey_slots):
        print(f"❌ Invalid slot index {slot_index}. Valid range: 0-{len(self.hotkey_slots)-1}")
        return False

    slot = self.hotkey_slots[slot_index]

    # Store the old ability data for logging
    old_ability = getattr(slot, 'ability_data', None)
    old_name = old_ability.get('name', 'Empty') if old_ability else 'Empty'

    # Update the slot's ability data
    slot.ability_data = ability_data.copy()  # Create a copy to avoid reference issues

    # Update the slot's visual appearance if needed
    if hasattr(slot, 'color') and ability_data:
        try:
            # Get color based on action type
            action_type = ability_data.get('action_type', 'Attack')
            slot.color = self._get_talent_action_color(action_type)
        except Exception as e:
            print(f"⚠️ Could not update slot color: {e}")

    # Log the change
    new_name = ability_data.get('name', 'Unknown') if ability_data else 'Empty'
    print(f"🔄 Hotkey slot {slot_index + 1}: '{old_name}' → '{new_name}'")

    # Update character state manager if available
    if hasattr(self, 'character_state_manager') and self.character_state_manager:
        try:
            active_character = self.character_state_manager.get_active_character()
            if active_character:
                # Update the character's hotkey abilities list
                if not hasattr(active_character, 'hotkey_abilities'):
                    active_character.hotkey_abilities = [None] * len(self.hotkey_slots)

                # Ensure the list is long enough
                while len(active_character.hotkey_abilities) <= slot_index:
                    active_character.hotkey_abilities.append(None)

                # Update the specific slot
                active_character.hotkey_abilities[slot_index] = ability_data.copy() if ability_data else None

                print(f"✅ Updated character's hotkey ability {slot_index + 1}")
        except Exception as e:
            print(f"⚠️ Could not update character state: {e}")

    return True

def hotkey_get_hotkey_slot_ability_data(self, slot_index: int) -> Optional[Dict[str, Any]]:
    """Get the ability_data for a specific hotkey slot."""
    if not hasattr(self, 'hotkey_slots') or not self.hotkey_slots:
        return None

    if slot_index < 0 or slot_index >= len(self.hotkey_slots):
        return None

    slot = self.hotkey_slots[slot_index]
    return getattr(slot, 'ability_data', None)

def create_hotkey_slots(self):
    """Create hotkey ability slots using master UI configuration."""
    if not URSINA_AVAILABLE:
        return

    # Use master UI configuration
    from src.core.ui.ui_config_manager import get_ui_config_manager
    ui_config = get_ui_config_manager()

    # Get configuration values from master config
    max_slots = ui_config.get('hotkey_system.max_interface_slots', 8)
    slot_size = ui_config.get('hotkey_system.slot_layout.slot_size', 0.06)
    slot_spacing = ui_config.get('hotkey_system.slot_layout.slot_spacing', 0.01)
    start_pos = ui_config.get_position('hotkey_system.slot_layout.start_position')

    # Colors from master config
    empty_color = ui_config.get_color('hotkey_system.visual_settings.empty_slot_color', '#404040')

    # Clear existing slots
    self._clear_hotkey_slots()

    # Create slots
    for i in range(max_slots):
        x_offset = i * (slot_size + slot_spacing)

        # Create slot button using master config
        slot_button = Button(
            parent=camera.ui,
            model=ui_config.get('models_and_textures.default_models.button', 'cube'),
            color=empty_color,
            scale=slot_size,
            position=(start_pos['x'] + x_offset, start_pos['y'], start_pos['z']),
            on_click=lambda slot_index=i: self._on_hotkey_slot_clicked(slot_index)
        )

        # Add hotkey number text using master config
        if ui_config.get('hotkey_system.display_options.show_hotkey_numbers', True):
            hotkey_text_color = ui_config.get_color('hotkey_system.visual_settings.hotkey_text_color', '#FFFF00')
            hotkey_text_scale = ui_config.get('hotkey_system.visual_settings.hotkey_text_scale', 0.3)
            text_pos = ui_config.get_position('hotkey_system.visual_settings.hotkey_text_position')

            hotkey_text = Text(
                text=str(i + 1),
                parent=slot_button,
                position=(text_pos['x'], text_pos['y'], text_pos['z']),
                scale=hotkey_text_scale,
                color=hotkey_text_color,
                origin=(0, 0)
            )
            slot_button.hotkey_text = hotkey_text

        # Initialize slot data
        slot_button.ability_data = None
        slot_button.tooltip = None
        slot_button.slot_index = i
        slot_button.enabled = False  # Start hidden

        self.hotkey_slots.append(slot_button)

def get_talent_action_color(self, action_type: str):
    """Get color for talent based on action type using unified configuration."""
    try:
        from src.core.assets.data_manager import get_action_item_color, convert_hex_to_ursina_color
        color_hex = get_action_item_color(action_type)
        return convert_hex_to_ursina_color(color_hex)
    except Exception as e:
        print(f"⚠️ Could not load unified colors for hotkey: {e}, using fallback")

        # Fallback color map
        color_map = {
            'Attack': color.red,
            'Magic': color.blue,
            'Spirit': color.yellow,
            'Move': color.green,
            'Inventory': color.orange
        }
        return color_map.get(action_type, color.white)

def handle_hotkey_activation(self, slot_index: int):
    """Handle hotkey activation from either mouse click or keyboard shortcut."""
    if slot_index >= len(self.hotkey_slots):
        print(f"❌ Invalid hotkey slot {slot_index + 1}")
        return

    slot = self.hotkey_slots[slot_index]
    ability_data = slot.ability_data

    if ability_data:
        # Check if slot is available (not disabled due to insufficient AP)
        if slot.disabled:
            print(f"🚫 Hotkey {slot_index + 1} unavailable (insufficient AP)")
            return

        # Get ability name for feedback (try talent resolution first)
        ability_name = "Unknown"
        talent_id = ability_data.get('talent_id')

        if talent_id:
            from src.core.assets.data_manager import get_data_manager
            data_manager = get_data_manager()
            talent_data = data_manager.get_talent(talent_id)
            if talent_data:
                ability_name = talent_data.name
        else:
            ability_name = ability_data.get('name', 'Unknown')

        print(f"🎯 Hotkey {slot_index + 1}: Activating {ability_name}")
        self._activate_ability(ability_data)
    else:
        print(f"❌ Empty hotkey slot {slot_index + 1}")

def activate_ability(self, ability_data: Dict[str, Any]):
    """Activate the specified ability by executing the specific talent."""
    if not self.active_unit:
        print("❌ No active unit selected")
        return

    # Check if this is talent_id reference or old format ability data
    talent_id = ability_data.get('talent_id')

    if talent_id:
        # New format: execute specific talent using unified system
        from src.core.assets.data_manager import get_data_manager
        from game.config.action_costs import ACTION_COSTS

        data_manager = get_data_manager()
        talent_data = data_manager.get_talent(talent_id)

        if not talent_data:
            print(f"❌ Talent '{talent_id}' not found")
            return

        # Check AP requirement
        required_ap = ACTION_COSTS.get_talent_cost(talent_data)
        current_ap = getattr(self.active_unit, 'ap', 0)

        if current_ap < required_ap:
            print(f"❌ Insufficient AP for {talent_data.name}: {current_ap}/{required_ap}")
            return

        ability_name = talent_data.name
        action_type = talent_data.action_type

        print(f"🔥 Executing unified talent: {ability_name} (ID: {talent_id}, Type: {action_type}, AP: {current_ap}/{required_ap})")
        self._execute_specific_talent(talent_data)
    else:
        # Try to find talent by name in the data manager (fallback for legacy without talent_id)
        from src.core.assets.data_manager import get_data_manager
        from game.config.action_costs import ACTION_COSTS

        ability_name = ability_data.get('name', 'Unknown Ability')
        action_type = ability_data.get('action_type', 'Attack')
        
        # First attempt to find matching talent by name and action type
        data_manager = get_data_manager()
        matching_talent = None
        
        for talent in data_manager.get_all_talents():
            if talent.name == ability_name and talent.action_type == action_type:
                matching_talent = talent
                break
        
        if matching_talent:
            print(f"🔄 Found matching talent '{ability_name}' - using unified system")
            
            # Check AP requirement using talent system
            required_ap = ACTION_COSTS.get_talent_cost(matching_talent)
            current_ap = getattr(self.active_unit, 'ap', 0)

            if current_ap < required_ap:
                print(f"❌ Insufficient AP for {matching_talent.name}: {current_ap}/{required_ap}")
                return

            print(f"🔥 Executing unified talent (fallback): {matching_talent.name} (Type: {action_type}, AP: {current_ap}/{required_ap})")
            self._execute_specific_talent(matching_talent)
        else:
            # Final fallback: use legacy action system (should be deprecated)
            print(f"⚠️ Using legacy action system for {ability_name} - consider adding talent_id")
            
            required_ap = ACTION_COSTS.get_action_cost(action_type)
            current_ap = getattr(self.active_unit, 'ap', 0)

            if current_ap < required_ap:
                print(f"❌ Insufficient AP for {ability_name}: {current_ap}/{required_ap}")
                return

            print(f"🔥 Activating legacy ability: {ability_name} (Action: {action_type}, AP: {current_ap}/{required_ap})")

            # Map talent action type to Unit Action
            if action_type == "Attack":
                self.handle_action_selection("Attack", self.active_unit)
            elif action_type == "Magic":
                self.handle_action_selection("Magic", self.active_unit)
            elif action_type == "Spirit":
                self.handle_action_selection("Spirit", self.active_unit)
            elif action_type == "Move":
                self.handle_action_selection("Move", self.active_unit)
            elif action_type == "Inventory":
                self.handle_action_selection("Inventory", self.active_unit)
            else:
                print(f"❌ Unknown action type: {action_type}")
                return

            print(f"   ✅ Unit Action '{action_type}' triggered for {self.active_unit.name}")

def talent_requires_targeting(self, talent_data):
    """Determine if a talent requires target selection."""
    #talent_requires_targeting(self, talent_data)
    effects = talent_data.effects
    action_type = talent_data.action_type

    # Check for effects that require targeting
    targeting_effects = [
        'base_damage', 'magical_damage', 'physical_damage', 'spiritual_damage',
        'healing_amount', 'healing', 'area_of_effect', 'range'
    ]

    # Check if any targeting effects are present
    has_targeting_effects = any(effect in effects for effect in targeting_effects)

    # Check if range is specified (range > 0 means targeting needed)
    has_range = int(effects.get('range', 0)) > 0

    # Magic and Attack actions typically require targeting unless self-only
    requires_targeting_by_type = action_type in ['Magic', 'Attack'] and not effects.get('self_target_only', False)

    return has_targeting_effects or has_range or requires_targeting_by_type

def hotkey_update_hotkey_slots(self):
    """Update hotkey slots with current active character's abilities and AP availability."""
    if not self.hotkey_slots:
        return

    # Get active character
    active_character = self.character_state_manager.get_active_character()

    if not active_character:
        # No active character, hide all slots
        for slot in self.hotkey_slots:
            slot.enabled = False
        return

    # Get character's hotkey abilities
    hotkey_abilities = active_character.hotkey_abilities
    hotkey_settings = self.hotkey_config.get('hotkey_system', {})
    visual_settings = hotkey_settings.get('visual_settings', {})

    # Get data manager for talent resolution
    from src.core.assets.data_manager import get_data_manager
    from game.config.action_costs import ACTION_COSTS
    data_manager = get_data_manager()

    # Colors
    empty_color = self._hex_to_color(visual_settings.get('empty_slot_color', '#404040'))
    disabled_color = self._hex_to_color('#202020')  # Darker gray for insufficient AP

    # Get current unit's AP
    current_ap = getattr(self.active_unit, 'ap', 0) if self.active_unit else 0

    # Update each slot
    for i, slot in enumerate(self.hotkey_slots):
        slot.enabled = True  # Show slot

        # FIXED: Handle sparse list with None values for empty slots
        if isinstance(hotkey_abilities, list) and i < len(hotkey_abilities) and hotkey_abilities[i] is not None:
            # Get ability data from the list
            ability_data = hotkey_abilities[i]
            slot.ability_data = ability_data

            # Check AP requirement
            required_ap = 0
            talent_id = ability_data.get('talent_id')

            if talent_id:
                # New format: get talent-specific AP cost
                talent_data = data_manager.get_talent(talent_id)
                if talent_data:
                    required_ap = ACTION_COSTS.get_talent_cost(talent_data)
            else:
                # Legacy format: get action type AP cost
                action_type = ability_data.get('action_type', 'Attack')
                required_ap = ACTION_COSTS.get_action_cost(action_type)

            # Set slot color and availability based on AP
            if current_ap >= required_ap:
                # Sufficient AP - normal color
                action_type = ability_data.get('action_type', 'Unknown')
                #slot.color = self._get_talent_action_color(action_type)
                slot.color = get_talent_action_color(self, action_type)
                slot.disabled = False
            else:
                # Insufficient AP - darker color and disabled
                slot.color = disabled_color
                slot.disabled = True

            # Create tooltip with ability data and AP info
            if hasattr(slot, 'tooltip') and slot.tooltip:
                destroy(slot.tooltip)

            ability_name = ability_data.get('name', 'Unknown Ability')
            ability_description = ability_data.get('description', 'No description available')
            action_type = ability_data.get('action_type', 'Unknown')

            tooltip_text = f"{ability_name}\n{ability_description}\nAction: {action_type}\nAP Cost: {required_ap}\nHotkey: {i + 1}"

            slot.tooltip = Tooltip(tooltip_text)
            slot.tooltip.background.color = color.hsv(0, 0, 0, .8)
        else:
            # Empty slot (None value or out of bounds)
            slot.ability_data = None
            slot.color = empty_color
            slot.disabled = False

            # Remove tooltip if exists
            if hasattr(slot, 'tooltip') and slot.tooltip:
                destroy(slot.tooltip)
                slot.tooltip = None
