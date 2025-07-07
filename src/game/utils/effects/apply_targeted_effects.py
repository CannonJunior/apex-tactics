"""
Apply Targeted Effects

"""

from typing import List, Dict, Any
from enum import Enum

try:
    from components.combat.damage import AttackType
except ImportError:
    # Fallback enum if import fails
    class AttackType(Enum):
        PHYSICAL = "physical"
        MAGICAL = "magical"
        SPIRITUAL = "spiritual"

def apply_targeted_effects(self, effects, target_units: List, spell_params: dict):
    """Apply all effects from a talent to the targeted units."""
    if not target_units:
        print("  No targets found in area.")
        return

    # Damage effects
    damage_effects = ['base_damage', 'magical_damage', 'physical_damage', 'spiritual_damage']
    for damage_type in damage_effects:
        if damage_type in effects:
            damage = int(effects[damage_type])
            guaranteed_hit = effects.get('guaranteed_hit', False)
            attack_type = self._get_attack_type_from_damage_effect(damage_type)

            for target_unit in target_units:
                if self._is_valid_damage_target(target_unit, effects):
                    if guaranteed_hit:
                        print(f"  {target_unit.name} takes {damage} {damage_type.replace('_', ' ')}! (guaranteed hit)")
                    else:
                        print(f"  {target_unit.name} takes {damage} {damage_type.replace('_', ' ')}!")
                    target_unit.take_damage(damage, attack_type)

                    if not target_unit.alive:
                        print(f"  {target_unit.name} has been defeated!")
                        self._remove_defeated_unit(target_unit)

    # Healing effects
    healing_effects = ['healing_amount', 'healing']
    for heal_type in healing_effects:
        if heal_type in effects:
            healing = int(effects[heal_type])

            for target_unit in target_units:
                if self._is_valid_healing_target(target_unit, effects):
                    old_hp = target_unit.hp
                    target_unit.hp = min(target_unit.max_hp, target_unit.hp + healing)
                    actual_healing = target_unit.hp - old_hp
                    print(f"  {target_unit.name} healed for {actual_healing} HP (now {target_unit.hp}/{target_unit.max_hp})")
                    # FIXED: Update health bar if this is the active unit
                    if (hasattr(self, 'active_unit') and target_unit == self.active_unit and 
                        hasattr(self, 'refresh_health_bar')):
                        self.refresh_health_bar()

    # MP restoration effects
    if 'mp_restoration' in effects:
        mp_restore = int(effects['mp_restoration'])
        for target_unit in target_units:
            if self._is_valid_mp_target(target_unit, effects):
                old_mp = target_unit.mp
                target_unit.mp = min(target_unit.max_mp, target_unit.mp + mp_restore)
                actual_restoration = target_unit.mp - old_mp
                print(f"  {target_unit.name} restored {actual_restoration} MP (now {target_unit.mp}/{target_unit.max_mp})")
                # FIXED: Update resource bar if this is the active unit
                if (hasattr(self, 'active_unit') and target_unit == self.active_unit and 
                    hasattr(self, 'refresh_resource_bar')):
                    self.refresh_resource_bar()

    # Buff effects (stat bonuses, damage reduction, etc.)
    if 'stat_bonus' in effects:
        stat_bonus = int(effects['stat_bonus'])
        duration = int(effects.get('duration', 5))
        affected_stats = effects.get('affected_stats', ['strength', 'finesse', 'wisdom'])

    # MP restoration effects
    if 'mp_restoration' in effects:
        mp_restore = int(effects['mp_restoration'])
        for target_unit in target_units:
            if self._is_valid_mp_target(target_unit, effects):
                old_mp = target_unit.mp
                target_unit.mp = min(target_unit.max_mp, target_unit.mp + mp_restore)
                actual_restoration = target_unit.mp - old_mp
                print(f"  {target_unit.name} restored {actual_restoration} MP (now {target_unit.mp}/{target_unit.max_mp})")
                # FIXED: Update resource bar if this is the active unit
                if (hasattr(self, 'active_unit') and target_unit == self.active_unit and 
                    hasattr(self, 'refresh_resource_bar')):
                    self.refresh_resource_bar()

    # Buff effects (stat bonuses, damage reduction, etc.)
    if 'stat_bonus' in effects:
        stat_bonus = int(effects['stat_bonus'])
        duration = int(effects.get('duration', 5))
        affected_stats = effects.get('affected_stats', ['strength', 'finesse', 'wisdom'])

        for target_unit in target_units:
            if self._is_valid_buff_target(target_unit, effects):
                print(f"  {target_unit.name} receives +{stat_bonus} to {', '.join(affected_stats)} for {duration} turns")
                # TODO: Implement temporary stat modifier system

    # Defense bonus effects
    defense_bonuses = ['magical_defense_bonus', 'spiritual_defense_bonus', 'physical_defense_bonus']
    for defense_type in defense_bonuses:
        if defense_type in effects:
            bonus = int(effects[defense_type])
            duration = int(effects.get('duration', 3))

            for target_unit in target_units:
                if self._is_valid_debuff_target(target_unit, effects):
                    defense_name = reduction_type.replace('_reduction', '').replace('_', ' ')
                    print(f"  {target_unit.name} loses -{reduction} {defense_name} for {duration} turns")
                    # TODO: Implement defense reduction system
