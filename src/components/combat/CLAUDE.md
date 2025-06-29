# Combat Components

## Overview

This directory contains components that implement the combat system for Apex Tactics. These components work together to provide a comprehensive turn-based tactical combat experience with multiple damage types, targeting systems, and defensive mechanics.

## Component Architecture

### Combat System Design
The combat system uses a modular approach where different aspects of combat are handled by separate components:
- **Attack Components** - Offensive capabilities and targeting
- **Damage Components** - Damage calculation and type resolution
- **Defense Components** - Defensive stats and damage mitigation

### Integration with Core Systems
Combat components integrate with:
- **UnitStatsComponent** - For base attributes and combat stats
- **EquipmentComponent** - For weapon/armor bonuses
- **MovementComponent** - For positioning and range calculation
- **ResourceComponents** - For HP/MP management

## Component Files

### `attack.py` - Attack System
Handles offensive combat mechanics:

#### AttackTarget Class
```python
@dataclass
class AttackTarget:
    unit_id: int
    position: Vector3
    distance: float
```
Represents potential targets for attacks with spatial information.

#### AttackComponent Features
- **Range Calculation** - Determines valid attack targets
- **Targeting System** - Line-of-sight and area-of-effect targeting
- **Attack Resolution** - Handles hit/miss calculations
- **Multi-Target Attacks** - Support for area-effect abilities

### `damage.py` - Damage System
Manages damage calculation and application:

#### Damage Types
- **Physical** - Strength-based melee and ranged attacks
- **Magical** - Wonder/Spirit-based spell damage
- **Spiritual** - Faith/Worthy-based divine damage

#### DamageResult Structure
```python
@dataclass
class DamageResult:
    damage_amount: int
    damage_type: AttackType
    is_critical: bool
    resistances_applied: List[str]
```

#### Damage Calculation
- **Base Damage** - From attacker's attributes
- **Weapon Bonuses** - Equipment modifications
- **Critical Hits** - Enhanced damage on lucky rolls
- **Resistance Application** - Defender damage reduction

### `defense.py` - Defense System
Handles damage mitigation and protection:

#### Defense Types
- **Physical Defense** - Armor and constitution
- **Magical Defense** - Magical resistance and wards
- **Spiritual Defense** - Divine protection and willpower

#### Defense Mechanics
- **Damage Reduction** - Flat reduction based on defense stats
- **Resistance Calculation** - Percentage-based damage mitigation
- **Armor Effectiveness** - Equipment-based protection
- **Defensive Stances** - Tactical positioning bonuses

## Combat Flow

### 1. Attack Initiation
```python
# Unit selects attack action
attack_component = attacker.get_component(AttackComponent)
valid_targets = attack_component.get_valid_targets(game_state)
```

### 2. Target Selection
```python
# Player/AI selects target(s)
selected_targets = attack_component.select_targets(target_positions)
```

### 3. Attack Resolution
```python
# Calculate hit chance and damage
for target in selected_targets:
    hit_result = attack_component.calculate_hit(target)
    if hit_result.hits:
        damage = calculate_damage(attacker, target, attack_type)
        apply_damage(target, damage)
```

### 4. Defense Application
```python
# Target's defense component processes incoming damage
defense_component = target.get_component(DefenseComponent)
final_damage = defense_component.mitigate_damage(damage_result)
target.take_damage(final_damage)
```

## Attribute Integration

### Physical Combat
Uses the physical attribute trio:
- **Strength** - Raw physical power for damage
- **Finesse** - Accuracy and critical hit chance
- **Fortitude** - Physical resilience and armor effectiveness

### Magical Combat
Uses the mental attribute trio:
- **Wisdom** - Magical knowledge and spell effectiveness
- **Wonder** - Raw magical power for damage
- **Spirit** - Magical resistance and mana efficiency

### Spiritual Combat
Uses the social attribute trio:
- **Faith** - Divine connection and spiritual power
- **Worthy** - Moral strength and divine favor
- **Speed** - Initiative and reaction time

## Combat Formulas

### Attack Damage
```python
# Physical Attack
base_damage = (strength + finesse) // 2
weapon_bonus = equipped_weapon.get('physical_attack', 0)
final_damage = base_damage + weapon_bonus + random(1, 6)

# Magical Attack  
base_damage = (wisdom + wonder) // 2
spell_bonus = equipped_focus.get('magical_attack', 0)
final_damage = base_damage + spell_bonus + random(1, 6)
```

### Defense Calculation
```python
# Physical Defense
base_defense = (fortitude + strength) // 3
armor_bonus = equipped_armor.get('physical_defense', 0)
total_defense = base_defense + armor_bonus

# Damage Mitigation
mitigated_damage = max(1, incoming_damage - total_defense)
```

### Range and Area Effects
```python
# Attack Range (from weapon)
attack_range = max(base_range, weapon.get('attack_range', 1))

# Effect Area (area-of-effect radius)
effect_radius = max(base_area, weapon.get('effect_area', 0))

# Target Selection
for position in combat_grid:
    if distance_to_attacker(position) <= attack_range:
        # Valid attack target
        if distance_to_target(position) <= effect_radius:
            # Affected by area attack
```

## Special Combat Mechanics

### Critical Hits
- **Trigger Condition** - High finesse or lucky roll
- **Damage Multiplier** - 1.5x to 2x base damage
- **Special Effects** - Additional status effects or bonuses

### Area-of-Effect Attacks
- **Target Selection** - Choose center point within range
- **Effect Radius** - All units within specified distance affected
- **Damage Distribution** - Full damage to primary target, reduced to secondary

### Status Effects
- **Buffs/Debuffs** - Temporary stat modifications
- **Damage Over Time** - Poison, burn, bleeding effects
- **Crowd Control** - Stun, sleep, paralysis effects

## Equipment Integration

### Weapon Effects
```python
# Spear example: extended range and area effect
weapon_stats = {
    'attack_range': 2,    # Can attack 2 tiles away
    'effect_area': 2,     # Hits 2-tile radius around target
    'physical_attack': 14 # Bonus damage
}
```

### Armor Protection
```python
# Chain Mail example: physical and magical defense
armor_stats = {
    'physical_defense': 15,  # Reduces physical damage
    'magical_defense': 3,    # Reduces magical damage
    'durability': 150        # Uses before breaking
}
```

## Combat Events

### Attack Events
- **AttackInitiated** - Attack sequence begins
- **TargetSelected** - Target(s) chosen for attack
- **AttackResolved** - Hit/miss determined
- **DamageCalculated** - Damage amount computed
- **DamageApplied** - Health reduced, effects applied

### Defense Events
- **DefenseTriggered** - Incoming attack detected
- **DamageResisted** - Defense calculations applied
- **ArmorDamaged** - Equipment durability reduced
- **CounterAttack** - Opportunity attack triggered

## Testing Combat Components

### Unit Tests
```python
def test_attack_damage_calculation():
    attacker = create_test_unit(strength=15, finesse=12)
    weapon = {'physical_attack': 10}
    damage = calculate_physical_damage(attacker, weapon)
    assert damage >= 24  # (15+12)//2 + 10 + 1

def test_defense_mitigation():
    defender = create_test_unit(fortitude=20)
    armor = {'physical_defense': 8}
    damage = apply_defense(50, defender, armor)
    assert damage < 50  # Some mitigation applied
```

### Integration Tests
```python
def test_complete_combat_sequence():
    attacker = create_unit_with_weapon("spear")
    defender = create_unit_with_armor("chain_mail")
    
    # Test full attack sequence
    targets = get_valid_targets(attacker, game_grid)
    assert defender in targets
    
    damage_dealt = execute_attack(attacker, defender)
    assert damage_dealt > 0
    assert defender.hp < defender.max_hp
```

## Best Practices

### Component Design
- Keep combat logic stateless where possible
- Use events for complex interactions between components
- Cache expensive calculations (hit chances, valid targets)
- Separate calculation from presentation/effects

### Balance Considerations
- Test combat math with various attribute combinations
- Ensure meaningful progression between equipment tiers
- Validate that defense scales appropriately with offense
- Consider edge cases (zero damage, maximum damage, etc.)

### Performance
- Precompute valid targets when possible
- Use efficient algorithms for area-of-effect calculations
- Cache frequently accessed attribute combinations
- Minimize object creation during combat resolution

### Extensibility
- Design for easy addition of new damage types
- Support flexible targeting patterns (line, cone, area)
- Allow for custom combat effects and modifiers
- Enable easy integration with new equipment types