# Systems Directory

## Overview

This directory contains the Entity-Component-System (ECS) systems that implement game logic by processing entities with specific component combinations. Systems contain the behavior and logic that operates on component data to create gameplay mechanics.

## ECS Systems Architecture

### System Design Principles
- **Data Processing**: Systems process component data, don't store it
- **Entity Queries**: Find entities with required component combinations
- **Stateless Logic**: Systems should be stateless processors
- **Performance Focus**: Efficiently iterate over large entity sets

### Base System Structure
```python
class MySystem(BaseSystem):
    def process(self, entities: EntityManager, delta_time: float):
        """Process all relevant entities each frame"""
        for entity in entities.with_components(RequiredComponent):
            component = entity.get_component(RequiredComponent)
            # Process component logic
```

## Current Systems

### `combat_system.py` - Combat Processing
Handles all combat-related calculations and interactions:

#### Core Responsibilities
- **Attack Resolution** - Process attack actions and calculate results
- **Damage Calculation** - Compute damage based on attacker/defender stats
- **Area Effects** - Handle splash damage and area-of-effect abilities
- **Combat Events** - Generate combat events for UI and audio systems

#### Key Components Processed
- **AttackComponent** - Offensive capabilities and targeting
- **DefenseComponent** - Defensive stats and damage mitigation
- **DamageComponent** - Damage calculation and type handling
- **AttributeStats** - Base attributes for combat calculations

#### System Features
```python
class CombatSystem(BaseSystem):
    def resolve_attack(self, attacker: Entity, targets: List[Entity]):
        """Resolve attack against multiple targets"""
        
    def calculate_damage(self, attacker: Entity, defender: Entity) -> DamageResult:
        """Calculate damage with all modifiers"""
        
    def apply_area_effect(self, center: Vector3, radius: float, effect: Effect):
        """Apply effects to all entities in area"""
```

### `movement_system.py` - Movement and Positioning
Manages unit movement, pathfinding, and spatial relationships:

#### Core Responsibilities
- **Movement Validation** - Check if moves are legal
- **Pathfinding** - Calculate optimal routes between positions
- **Position Updates** - Update entity positions and spatial relationships
- **Movement Events** - Generate events for position changes

#### Key Components Processed
- **MovementComponent** - Movement capabilities and constraints
- **Transform** - Current position and facing direction
- **TacticalMovementComponent** - Tactical movement options

### `stat_system.py` - Statistics Management
Handles attribute calculations, modifiers, and derived stats:

#### Core Responsibilities
- **Stat Calculation** - Compute derived stats from base attributes
- **Modifier Application** - Apply temporary and permanent modifiers
- **Equipment Integration** - Include equipment bonuses in calculations
- **Resource Management** - Handle HP, MP, AP regeneration and consumption

#### Key Components Processed
- **AttributeStats** - Core 9-attribute system
- **ModifierComponent** - Temporary and permanent stat changes
- **ResourceComponent** - Health, mana, action points
- **EquipmentComponent** - Equipment-based stat modifications

## System Processing Flow

### Frame Processing
```python
def game_update(delta_time: float):
    # Process systems in dependency order
    stat_system.process(entities, delta_time)      # Update stats first
    movement_system.process(entities, delta_time)  # Handle movement
    combat_system.process(entities, delta_time)    # Resolve combat
    # Additional systems...
```

### System Dependencies
1. **Stat System** - Must run first to calculate current stats
2. **Movement System** - Depends on stats for movement calculations
3. **Combat System** - Depends on stats and positions
4. **Visual Systems** - Depend on all data systems

### Event Handling
Systems communicate through events:
```python
class CombatSystem(BaseSystem):
    def process(self, entities, delta_time):
        # Process combat and generate events
        if damage_dealt:
            self.event_manager.emit(DamageDealtEvent(target, damage))
            self.event_manager.emit(HealthChangedEvent(target, new_hp))
```

## System Implementation Patterns

### Entity Queries
```python
# Find entities with specific components
combat_entities = entities.with_components(
    AttributeStats, 
    AttackComponent, 
    Transform
)

# Process only relevant entities
for entity in combat_entities:
    stats = entity.get_component(AttributeStats)
    attack = entity.get_component(AttackComponent)
    transform = entity.get_component(Transform)
    # Process combat logic
```

### Component Communication
```python
# Systems coordinate through component data
def update_equipment_stats(entity: Entity):
    stats = entity.get_component(AttributeStats)
    equipment = entity.get_component(EquipmentComponent)
    
    if equipment and equipment.equipped_weapon:
        weapon = equipment.equipped_weapon
        stats.apply_equipment_bonus(weapon.stats)
```

### Performance Optimization
```python
# Cache expensive calculations
class CombatSystem(BaseSystem):
    def __init__(self):
        self.damage_cache = {}
        
    def calculate_damage(self, attacker_id, defender_id):
        cache_key = (attacker_id, defender_id)
        if cache_key in self.damage_cache:
            return self.damage_cache[cache_key]
        
        # Calculate and cache result
        damage = self._compute_damage(attacker, defender)
        self.damage_cache[cache_key] = damage
        return damage
```

## Combat System Details

### Attack Resolution Process
1. **Target Validation** - Ensure targets are in range and valid
2. **Hit Calculation** - Determine if attack hits based on accuracy
3. **Damage Calculation** - Compute damage including all modifiers
4. **Defense Application** - Apply defender's damage reduction
5. **Effect Application** - Apply damage and any special effects

### Area Effect Processing
```python
class AreaEffectSystem:
    def apply_area_effect(self, center: Vector3, radius: float, effect: Effect):
        """Apply effect to all entities within radius"""
        affected_entities = self.get_entities_in_radius(center, radius)
        
        for entity in affected_entities:
            distance = Vector3.distance(entity.position, center)
            effect_strength = self.calculate_falloff(distance, radius)
            self.apply_effect(entity, effect, effect_strength)
```

### Damage Type Resolution
```python
def resolve_damage_types(damage: DamageResult, defender: Entity) -> int:
    """Apply type-specific damage calculations"""
    defense = defender.get_component(DefenseComponent)
    
    if damage.damage_type == AttackType.PHYSICAL:
        return max(1, damage.amount - defense.physical_defense)
    elif damage.damage_type == AttackType.MAGICAL:
        return max(1, damage.amount - defense.magical_defense)
    elif damage.damage_type == AttackType.SPIRITUAL:
        return max(1, damage.amount - defense.spiritual_defense)
```

## Movement System Details

### Pathfinding Integration
```python
class MovementSystem(BaseSystem):
    def calculate_movement_path(self, start: Vector3, end: Vector3, 
                              movement_points: int) -> List[Vector3]:
        """Calculate optimal path within movement constraints"""
        
    def validate_movement(self, entity: Entity, destination: Vector3) -> bool:
        """Check if movement is legal for entity"""
        
    def update_position(self, entity: Entity, new_position: Vector3):
        """Update entity position and notify other systems"""
```

### Movement Constraints
- **Movement Points** - Limit distance per turn
- **Terrain** - Different movement costs for terrain types
- **Obstacles** - Block movement through certain positions
- **Unit Collision** - Prevent multiple units in same space

## Stat System Details

### Attribute Calculations
```python
class StatSystem(BaseSystem):
    def update_derived_stats(self, entity: Entity):
        """Recalculate all derived stats"""
        stats = entity.get_component(AttributeStats)
        equipment = entity.get_component(EquipmentComponent)
        modifiers = entity.get_component(ModifierComponent)
        
        # Base calculations
        stats.update_derived_stats()
        
        # Apply equipment bonuses
        if equipment:
            stats.apply_equipment_bonuses(equipment)
            
        # Apply temporary modifiers
        if modifiers:
            stats.apply_modifiers(modifiers)
```

### Resource Management
```python
def update_resources(self, entity: Entity, delta_time: float):
    """Handle resource regeneration and constraints"""
    resources = entity.get_component(ResourceComponent)
    
    # Regenerate mana over time
    if resources.mp < resources.max_mp:
        regen_rate = self.calculate_mp_regen(entity)
        resources.mp = min(resources.max_mp, 
                          resources.mp + regen_rate * delta_time)
    
    # Handle action point refresh
    if self.is_new_turn():
        resources.ap = resources.max_ap
```

## Adding New Systems

### 1. Define System Class
```python
class MyNewSystem(BaseSystem):
    def __init__(self):
        super().__init__()
        self.required_components = [RequiredComponent]
    
    def process(self, entities: EntityManager, delta_time: float):
        for entity in entities.with_components(*self.required_components):
            self.process_entity(entity, delta_time)
    
    def process_entity(self, entity: Entity, delta_time: float):
        # System-specific logic
        pass
```

### 2. Register with Game Engine
```python
# Add to main game loop
game_engine.add_system(MyNewSystem())
```

### 3. Define System Dependencies
```python
# Ensure systems run in correct order
system_dependencies = {
    'stat_system': [],
    'movement_system': ['stat_system'],
    'combat_system': ['stat_system', 'movement_system'],
    'my_new_system': ['stat_system']
}
```

## Testing Systems

### Unit Testing
```python
def test_combat_damage_calculation():
    # Create test entities with components
    attacker = create_test_entity_with_stats(strength=15)
    defender = create_test_entity_with_defense(physical_defense=5)
    
    # Test system logic
    combat_system = CombatSystem()
    damage = combat_system.calculate_damage(attacker, defender)
    
    assert damage > 0
    assert damage < 100  # Reasonable damage range
```

### Integration Testing
```python
def test_full_combat_sequence():
    # Test complete combat flow
    combat_system = CombatSystem()
    movement_system = MovementSystem()
    
    # Setup test scenario
    attacker = create_spear_wielder()
    defender = create_armored_unit()
    
    # Execute full sequence
    movement_system.move_unit(attacker, attack_position)
    combat_result = combat_system.execute_attack(attacker, defender)
    
    # Verify results
    assert combat_result.damage_dealt > 0
    assert defender.hp < defender.max_hp
```

## Best Practices

### Performance
- Process only entities that need updating
- Cache expensive calculations when possible
- Use efficient data structures for entity queries
- Profile system performance regularly

### Maintainability
- Keep systems focused on single responsibilities
- Use clear naming for system methods
- Document system dependencies and processing order
- Separate complex logic into helper methods

### Debugging
- Add logging for important system operations
- Provide debug visualization for system state
- Include validation checks for component data
- Create debug commands for system testing