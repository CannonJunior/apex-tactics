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

    # Create modal window
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
    magic_spell_name = self.active_unit.magic_spell_name if hasattr(self.active_unit, 'magic_spell_name') else "Magic Spell"

    # Create modal window
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
