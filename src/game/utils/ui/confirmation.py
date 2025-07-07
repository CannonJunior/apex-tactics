"""
Confirmations

"""

def show_attack_confirmation(self, target_x: int, target_y: int):
    """Show modal to confirm attack on target tile."""
    if not self.active_unit or not self.attack_target_tile:
        return

    # Find units that would be affected by the attack
    affected_units = self.get_units_in_effect_area(target_x, target_y)
    unit_list = affected_units  # Move unit_list declaration here

    # Set the targeted units for UI display
    self.set_targeted_units(unit_list)

    # Create confirmation buttons
    confirm_btn = Button(
        text=self._get_button_config('attack_confirmation', 'confirm').get('text', 'Confirm Attack'),
        color=self._get_button_color('attack_confirmation', 'confirm', color.red)
    )
    cancel_btn = Button(
        text=self._get_button_config('attack_confirmation', 'cancel').get('text', 'Cancel'),
        color=self._get_button_color('attack_confirmation', 'cancel', color.gray)
    )

    # Store attack data for keyboard handling
    self._current_attack_data = {
        'target_x': target_x,
        'target_y': target_y,
        'affected_units': unit_list
    }

    # Set up button callbacks
    def confirm_attack():
        self._confirm_current_attack()

    def cancel_attack():
        self._cancel_current_attack()

    confirm_btn.on_click = confirm_attack
    cancel_btn.on_click = cancel_attack

    # Create modal content
    unit_names = ", ".join([unit.name for unit in unit_list]) if unit_list else "No units"

    # FIXED: Use talent-specific information if available
    if hasattr(self, 'current_talent_data') and self.current_talent_data:
        talent_data = self.current_talent_data
        talent_name = talent_data.name
        effects = talent_data.effects
        
        # DEBUG: Log talent data structure for verification
        print(f"🔍 CONFIRMATION MODAL DEBUG - Attack:")
        print(f"   Talent name: {talent_name}")
        print(f"   Talent effects: {effects}")
        print(f"   Talent cost: {getattr(talent_data, 'cost', 'NO COST DATA')}")
        
        # FIXED: Get damage from talent effects using correct JSON structure
        damage_value = (effects.get('base_damage', 0) or 
                       effects.get('physical_damage', 0) or 
                       effects.get('magical_damage', 0) or 
                       effects.get('spiritual_damage', 0))
        
        # If no talent damage found, use unit's base attack as fallback
        if damage_value == 0:
            damage_value = self.active_unit.physical_attack
        
        title_text = f'Confirm {talent_data.action_type}: {talent_name}'
        action_text = f'{self.active_unit.name} uses {talent_name} on tile ({target_x}, {target_y})'
        damage_text = f'Talent damage: {damage_value}'
        
        # Add cost information if available (FIXED: use dataclass attributes)
        cost_info = []
        if talent_data.cost:
            if talent_data.cost.get('mp_cost', 0) > 0:
                cost_info.append(f"MP cost: {talent_data.cost['mp_cost']}")
            if talent_data.cost.get('ap_cost', 0) > 0:
                cost_info.append(f"AP cost: {talent_data.cost['ap_cost']}")
            if talent_data.cost.get('talent_points', 0) > 0:
                cost_info.append(f"TP cost: {talent_data.cost['talent_points']}")
        
        content_items = [
            Text(action_text),
            Text(damage_text)
        ]
        if cost_info:
            content_items.append(Text(', '.join(cost_info)))
        content_items.extend([
            Text(f'Units in effect area: {unit_names}'),
            confirm_btn,
            cancel_btn
        ])
        
        # Create modal window with talent information
        self.attack_modal = WindowPanel(
            title=title_text,
            content=tuple(content_items),
            popup=True
        )
    else:
        # Fallback to original attack information
        self.attack_modal = WindowPanel(
            title='Confirm Attack',
            content=(
                Text(f'{self.active_unit.name} attacks tile ({target_x}, {target_y})'),
                Text(f'Attack damage: {self.active_unit.physical_attack}'),
                Text(f'Units in effect area: {unit_names}'),
                confirm_btn,
                cancel_btn
            ),
            popup=True
        )

    # Center the window panel
    self.attack_modal.y = self.attack_modal.panel.scale_y / 2 * self.attack_modal.scale_y
    self.attack_modal.layout()

def show_magic_confirmation(self, target_x: int, target_y: int):
    """Show modal to confirm magic on target tile."""
    if not self.active_unit or not self.magic_target_tile:
        return

    # Find units that would be affected by the magic
    affected_units = self.get_units_in_magic_effect_area(target_x, target_y)
    unit_list = affected_units

    # Set the targeted units for UI display
    self.set_targeted_units(unit_list)

    # Create confirmation buttons
    confirm_btn = Button(
        text=self._get_button_config('magic_confirmation', 'confirm').get('text', 'Confirm Magic'),
        color=self._get_button_color('magic_confirmation', 'confirm', color.blue)
    )
    cancel_btn = Button(
        text=self._get_button_config('magic_confirmation', 'cancel').get('text', 'Cancel'),
        color=self._get_button_color('magic_confirmation', 'cancel', color.gray)
    )

    # Store magic data for keyboard handling
    self._current_magic_data = {
        'target_x': target_x,
        'target_y': target_y,
        'affected_units': unit_list
    }

    # Set up button callbacks
    def confirm_magic():
        self._confirm_current_magic()

    def cancel_magic():
        self._cancel_current_magic()

    confirm_btn.on_click = confirm_magic
    cancel_btn.on_click = cancel_magic

    # Create modal content
    unit_names = ", ".join([unit.name for unit in unit_list]) if unit_list else "No units"

    # FIXED: Use talent-specific information if available
    if hasattr(self, 'current_talent_data') and self.current_talent_data:
        talent_data = self.current_talent_data
        talent_name = talent_data.name
        effects = talent_data.effects
        
        # DEBUG: Log talent data structure for verification
        print(f"🔍 CONFIRMATION MODAL DEBUG - Magic:")
        print(f"   Talent name: {talent_name}")
        print(f"   Talent effects: {effects}")
        print(f"   Talent cost: {getattr(talent_data, 'cost', 'NO COST DATA')}")
        
        # FIXED: Get damage from talent effects using correct JSON structure  
        damage_value = (effects.get('base_damage', 0) or 
                       effects.get('magical_damage', 0) or 
                       effects.get('spiritual_damage', 0) or
                       effects.get('physical_damage', 0))
        
        # Check for healing instead of damage (using correct JSON structure)
        healing_value = effects.get('healing_amount', 0) or effects.get('healing', 0)
        
        # If no talent damage found, use unit's base attack as fallback
        if damage_value == 0 and healing_value == 0:
            damage_value = self.active_unit.magical_attack
        
        title_text = f'Confirm {talent_data.action_type}: {talent_name}'
        action_text = f'{self.active_unit.name} casts {talent_name} on tile ({target_x}, {target_y})'
        
        # Show damage or healing
        if healing_value > 0:
            effect_text = f'Healing amount: {healing_value}'
        else:
            effect_text = f'Magic damage: {damage_value}'
        
        # Get MP cost from talent data (FIXED: use dataclass attributes)
        mp_cost = 0
        if talent_data.cost:
            mp_cost = talent_data.cost.get('mp_cost', 0)
        elif hasattr(self, 'current_spell_params') and self.current_spell_params:
            mp_cost = self.current_spell_params.get('mp_cost', 0)
        else:
            mp_cost = getattr(self.active_unit, 'magic_mp_cost', 0)
        
        # Add cost information (FIXED: use dataclass attributes)
        cost_info = []
        if mp_cost > 0:
            cost_info.append(f"MP cost: {mp_cost}")
        if talent_data.cost and talent_data.cost.get('ap_cost', 0) > 0:
            cost_info.append(f"AP cost: {talent_data.cost['ap_cost']}")
        if talent_data.cost and talent_data.cost.get('talent_points', 0) > 0:
            cost_info.append(f"TP cost: {talent_data.cost['talent_points']}")
        
        content_items = [
            Text(action_text),
            Text(effect_text)
        ]
        if cost_info:
            content_items.append(Text(', '.join(cost_info)))
        content_items.extend([
            Text(f'Units in effect area: {unit_names}'),
            confirm_btn,
            cancel_btn
        ])
        
        # Create modal window with talent information
        self.magic_modal = WindowPanel(
            title=title_text,
            content=tuple(content_items),
            popup=True
        )
    else:
        # Fallback to original magic information
        magic_spell_name = self.active_unit.magic_spell_name if hasattr(self.active_unit, 'magic_spell_name') else "Magic Spell"
        self.magic_modal = WindowPanel(
            title='Confirm Magic',
            content=(
                Text(f'{self.active_unit.name} casts {magic_spell_name} on tile ({target_x}, {target_y})'),
                Text(f'Magic damage: {self.active_unit.magical_attack}'),
                Text(f'MP cost: {self.active_unit.magic_mp_cost}'),
                Text(f'Units in effect area: {unit_names}'),
                confirm_btn,
                cancel_btn
            ),
            popup=True
        )

    # Center the window panel
    self.magic_modal.y = self.magic_modal.panel.scale_y / 2 * self.magic_modal.scale_y
    self.magic_modal.layout()
