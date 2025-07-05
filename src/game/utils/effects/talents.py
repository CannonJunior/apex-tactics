"""
Talents and Effects
TODO:
talent_requires_targeting
build_spell_params_from_effects
"""

from core.assets.talent_type_config import get_talent_type_config
from ursina import Entity, color, destroy, Button, Text, WindowPanel, camera, Tooltip

def execute_specific_talent(self, talent_data):
    """Execute a specific talent with its unique effects."""
    talent_name = talent_data.name
    talent_id = talent_data.id
    effects = talent_data.effects
    cost = talent_data.cost

    print(f"💫 Executing '{talent_name}' with specific effects:")

    # Check costs and apply them
    mp_cost = cost.get('mp_cost', 0)
    if mp_cost > 0:
        if self.active_unit.mp < mp_cost:
            print(f"❌ Not enough MP! Need {mp_cost}, have {self.active_unit.mp}")
            return
        self.active_unit.mp -= mp_cost
        print(f"   💙 Consumed {mp_cost} MP (remaining: {self.active_unit.mp})")

    # Execute talent using generalized effect system
    self._execute_talent_effects(talent_data)

    # MCP Integration Hook (Phase 3 - Talent Execution Hook)
    try:
        from ...config.feature_flags import FeatureFlags
        if (FeatureFlags.USE_MCP_TOOLS and 
            hasattr(self, 'mcp_integration_manager') and 
            self.mcp_integration_manager):
            
            # Notify MCP system of talent execution for learning
            talent_info = {
                'id': talent_id,
                'name': talent_name,
                'action_type': talent_data.action_type,
                'effects': effects,
                'cost': cost
            }
            self.mcp_integration_manager.notify_talent_executed(talent_info)
    except Exception as e:
        print(f"⚠️ MCP notification failed: {e}")

    print(f"   ✅ '{talent_name}' execution completed")

def execute_talent_effects(self, talent_data):
    """Execute talent using generalized effect system supporting multiple effects."""
    talent_name = talent_data.name
    action_type = talent_data.action_type
    effects = talent_data.effects

    print(f"   ✨ Executing '{talent_name}' ({action_type})...")

    # Check if this talent requires targeting (magic/attack/spirit with range)
    requires_targeting = self._talent_requires_targeting(talent_data)

    if requires_targeting:
        # Set up targeting mode with talent parameters
        spell_params = self._build_spell_params_from_effects(talent_data)
        self._setup_talent_magic_mode(talent_data, spell_params)
    else:
        # Execute immediate effects (self-targeting or passive)
        self._apply_immediate_effects(talent_data)

def talent_requires_targeting(self, talent_data):
    """Determine if a talent requires target selection."""
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

def build_spell_params_from_effects(self, talent_data):
    """Build spell parameters from talent effects for targeting mode."""
    effects = talent_data.effects
    talent_name = talent_data.name

    spell_params = {
        'spell_name': talent_name,
        'area_of_effect': self._parse_area_of_effect(effects.get('area_of_effect', 1)),
        'range': int(effects.get('range', 3)),
        'mp_cost': int(talent_data.cost.get('mp_cost', 0)),
    }

    # Add damage if present
    if 'base_damage' in effects:
        spell_params['damage'] = int(effects['base_damage'])
    elif 'magical_damage' in effects:
        spell_params['damage'] = int(effects['magical_damage'])
    elif 'physical_damage' in effects:
        spell_params['damage'] = int(effects['physical_damage'])
    elif 'spiritual_damage' in effects:
        spell_params['damage'] = int(effects['spiritual_damage'])

    # Add healing if present
    if 'healing_amount' in effects or 'healing' in effects:
        spell_params['healing'] = int(effects.get('healing_amount', effects.get('healing', 0)))
        spell_params['target_type'] = 'ally'

    # Add special properties
    if effects.get('guaranteed_hit', False):
        spell_params['guaranteed_hit'] = True

    return spell_params

def apply_immediate_effects(self, talent_data):
    """Apply effects that don't require targeting (self-buffs, instant effects)."""
    effects = talent_data.effects
    talent_name = talent_data.name

    # MP restoration
    if 'mp_restoration' in effects:
        mp_restore = int(effects['mp_restoration'])
        old_mp = self.active_unit.mp
        self.active_unit.mp = min(self.active_unit.max_mp, self.active_unit.mp + mp_restore)
        actual_restoration = self.active_unit.mp - old_mp
        print(f"   💙 Restored {actual_restoration} MP (now {self.active_unit.mp}/{self.active_unit.max_mp})")

    # HP restoration (self-healing)
    if 'hp_restoration' in effects:
        hp_restore = int(effects['hp_restoration'])
        old_hp = self.active_unit.hp
        self.active_unit.hp = min(self.active_unit.max_hp, self.active_unit.hp + hp_restore)
        actual_restoration = self.active_unit.hp - old_hp
        print(f"   ❤️  Restored {actual_restoration} HP (now {self.active_unit.hp}/{self.active_unit.max_hp})")

    # Stat bonuses (temporary buffs)
    if 'stat_bonus' in effects:
        stat_bonus = int(effects['stat_bonus'])
        duration = int(effects.get('duration', 5))
        affected_stats = effects.get('affected_stats', ['strength', 'finesse', 'wisdom'])
        print(f"   🎆 Applied +{stat_bonus} to {', '.join(affected_stats)} for {duration} turns")
        # TODO: Implement temporary stat modifier system

    # Damage reduction buffs
    if 'damage_reduction' in effects:
        reduction = int(effects['damage_reduction'])
        duration = int(effects.get('duration', 3))
        print(f"   🛡️  Applied {reduction} damage reduction for {duration} turns")
        # TODO: Implement damage reduction system

    # Attack/accuracy bonuses for combat talents
    if 'attack_bonus' in effects or 'accuracy_bonus' in effects:
        attack_bonus = effects.get('attack_bonus', 0)
        accuracy_bonus = effects.get('accuracy_bonus', 0)
        damage_mult = effects.get('damage_multiplier', 1.0)
        print(f"   ⚔️  Combat bonuses: +{attack_bonus} attack, +{accuracy_bonus}% accuracy, {damage_mult}x damage")
        # Trigger attack mode with bonuses
        self.handle_action_selection("Attack", self.active_unit)

    # Stress reduction
    if 'stress_reduction' in effects:
        stress_reduction = int(effects['stress_reduction'])
        print(f"   🧘 Reduced stress by {stress_reduction}")
        # TODO: Implement stress system

    # Defense bonuses
    if 'magical_defense_bonus' in effects or 'spiritual_defense_bonus' in effects:
        mag_def = effects.get('magical_defense_bonus', 0)
        spr_def = effects.get('spiritual_defense_bonus', 0)
        duration = int(effects.get('duration', 3))
        print(f"   🛡️  Defense bonuses: +{mag_def} magical, +{spr_def} spiritual for {duration} turns")
        # TODO: Implement defense bonus system

    print(f"   ✅ '{talent_name}' effects applied!")

def setup_talent_magic_mode(self, talent_data, spell_params):
    """Set up magic mode with talent-specific parameters."""
    # Store the current talent being cast
    self.current_talent_data = talent_data
    self.current_spell_params = spell_params

    # Store original magic properties for restoration
    self._original_magic_range = self.active_unit.magic_range
    self._original_magic_effect_area = self.active_unit.magic_effect_area
    self._original_magic_spell_name = getattr(self.active_unit, 'magic_spell_name', 'Magic Spell')
    self._original_magic_mp_cost = self.active_unit.magic_mp_cost

    # Store talent-specific magic properties on the unit temporarily (ensure integers)
    # Handle case where spell_params might be None
    if spell_params is None:
        spell_params = {}
    
    self.active_unit._talent_magic_range = int(spell_params.get('range', 3))
    self.active_unit._talent_magic_effect_area = int(spell_params.get('area_of_effect', 1))
    self.active_unit.magic_spell_name = spell_params.get('spell_name', 'Talent Spell')
    self.active_unit._talent_magic_mp_cost = int(spell_params.get('mp_cost', 10))

    # Enter talent mode based on talent type
    talent_type = talent_data.action_type
    self.current_mode = talent_type.lower()
    self._handle_talent(self.active_unit, talent_type)

    print(f"   🎯 Magic mode: {spell_params.get('spell_name')} targeting enabled!")
    print(f"   📏 Range: {self.active_unit._talent_magic_range}, Area: {self.active_unit._talent_magic_effect_area}")

def restore_original_magic_properties(self):
    """Restore unit's original magic properties after talent casting."""
    if hasattr(self, '_original_magic_spell_name'):
        self.active_unit.magic_spell_name = self._original_magic_spell_name

        # Clean up temporary attributes from unit
        if hasattr(self.active_unit, '_talent_magic_range'):
            delattr(self.active_unit, '_talent_magic_range')
        if hasattr(self.active_unit, '_talent_magic_effect_area'):
            delattr(self.active_unit, '_talent_magic_effect_area')
        if hasattr(self.active_unit, '_talent_magic_mp_cost'):
            delattr(self.active_unit, '_talent_magic_mp_cost')

        # Clean up temporary attributes from controller
        delattr(self, '_original_magic_range')
        delattr(self, '_original_magic_effect_area')
        delattr(self, '_original_magic_spell_name')
        delattr(self, '_original_magic_mp_cost')

    # Clear talent-specific data
    self.current_talent_data = None
    self.current_spell_params = None

def handle_talent(self, unit, talent_type: str):
    """Handle talent activation with type-specific highlighting and behavior."""
    if not unit:
        return

    # Get talent type configuration
    talent_config = get_talent_type_config()

    # Get talent-specific range or fall back to type default
    talent_range = getattr(unit, '_talent_magic_range', talent_config.get_default_range(talent_type))

    # Get highlighting color for this talent type
    range_color = talent_config.get_range_color(talent_type)
    color_name = talent_config.get_highlighting_config(talent_type).get('range_color_name', 'blue')

    print(f"{unit.name} entering {talent_type} talent mode. Range: {talent_range}")

    # Check if this talent type requires targeting
    if talent_config.requires_targeting(talent_type):
        # Clear existing highlights and show talent range with type-specific color
        self.clear_highlights()
        self.highlight_active_unit()
        self._highlight_talent_range(unit, talent_type, range_color)

        print(f"Click on a target within {color_name} highlighted tiles to use {talent_type} talent.")
    else:
        # No targeting required - execute immediately
        print(f"{talent_type} talent activated without targeting.")
        # TODO: Execute non-targeting talents immediately

def highlight_talent_range(self, unit, talent_type: str, highlight_color):
    """Highlight the talent-specific range around the unit with type-specific color."""
    if not unit:
        return

    # Get talent-specific range or fall back to type default
    talent_config = get_talent_type_config()
    talent_range = getattr(unit, '_talent_magic_range', talent_config.get_default_range(talent_type))

    # Clear existing highlights first
    self.clear_highlights()

    for x in range(self.grid.width):
        for y in range(self.grid.height):
            # Calculate Manhattan distance from unit to tile
            distance = abs(x - unit.x) + abs(y - unit.y)

            # Highlight tiles within talent range (excluding unit's own tile)
            if distance <= talent_range and distance > 0:
                # Check if tile is within grid bounds
                if 0 <= x < self.grid.width and 0 <= y < self.grid.height:
                    # Create highlight overlay entity with type-specific color
                    highlight = Entity(
                        model='cube',
                        color=highlight_color,
                        scale=(0.9, 0.2, 0.9),
                        position=(x + 0.5, 0, y + 0.5),  # Same height as grid tiles
                        alpha=1.0  # Same transparency as standard highlighting
                    )
                    # Store in a list for cleanup
                    if not hasattr(self, 'highlight_entities'):
                        self.highlight_entities = []
                    self.highlight_entities.append(highlight)
