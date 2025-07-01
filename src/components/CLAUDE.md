# Components Directory

## Overview

This directory contains all Entity-Component-System (ECS) components for Apex Tactics. Components define the data and properties that entities can have, implementing a modular architecture where functionality is composed rather than inherited.

## ECS Architecture

### Component Design Principles
- **Data-focused**: Components store data, not behavior
- **Modular**: Mix and match components for different entity types
- **Serializable**: All components support save/load operations
- **Loosely Coupled**: Components don't directly depend on each other

### Base Component
All components inherit from `BaseComponent`:
```python
@dataclass
class YourComponent(BaseComponent):
    def __init__(self, ...):
        super().__init__()
        # Component initialization
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for save/load"""
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Deserialize from save data"""
```

## Component Categories

### `/combat/` - Combat System Components
Combat-related data and mechanics:
- **`attack.py`** - Attack capabilities and bonuses
- **`damage.py`** - Damage calculation and types
- **`defense.py`** - Defensive stats and resistances

**Purpose**: Modular combat system where entities can have different combinations of combat abilities.

### `/equipment/` - Equipment Management
Equipment and item handling:
- **`equipment.py`** - Individual equipment pieces and stats
- **`equipment_manager.py`** - Equipment slots and management

**Purpose**: Flexible equipment system supporting different slot configurations and stat modifications.

### `/gameplay/` - Core Gameplay Mechanics
Essential gameplay systems:
- **`unit_stats.py`** - Core unit attributes and combat stats
- **`unit_type.py`** - Unit type bonuses and classifications
- **`tactical_movement.py`** - Movement and positioning mechanics

**Purpose**: Fundamental gameplay components used by most entities.

### `/movement/` - Movement System
Position and movement mechanics:
- **`movement.py`** - Position tracking and movement capabilities

**Purpose**: Spatial gameplay components for tactical positioning.

### `/stats/` - Attribute System
Character attributes and modifiers:
- **`attributes.py`** - Core attribute system (9-attribute model)
- **`modifiers.py`** - Temporary and permanent stat modifications
- **`resources.py`** - Health, mana, action points management

**Purpose**: Flexible stat system supporting complex character progression.

### `/visual/` - Visual Representation
Visual appearance and effects:
- **Future**: Animation, rendering, visual effects components

**Purpose**: Separates visual representation from game logic.

## Component Usage Patterns

### Entity Composition
```python
# Create a player character entity
player_entity = Entity()

# Add components for different capabilities
player_entity.add_component(UnitStatsComponent("Hero", UnitType.HEROMANCER))
player_entity.add_component(EquipmentComponent())
player_entity.add_component(CombatComponent())
player_entity.add_component(MovementComponent())
```

### Cross-Component Communication
Components communicate through:
1. **Properties**: Computed values based on component data
2. **Events**: System-mediated component interactions
3. **Queries**: Systems finding entities with specific components

### Stat Calculation Example
```python
# UnitStatsComponent calculates attack including equipment
@property
def physical_attack(self):
    base = self.strength + self.finesse
    
    # Get equipment bonus from EquipmentComponent
    equipment = self.entity.get_component(EquipmentComponent)
    if equipment and equipment.equipped_weapon:
        base += equipment.equipped_weapon.get('physical_attack', 0)
    
    return base
```

## Component Lifecycle

### Creation
```python
component = ComponentClass(initial_data)
entity.add_component(component)
```

### Updates
Systems process components each frame:
```python
# CombatSystem processes all entities with CombatComponent
for entity in entities_with(CombatComponent):
    combat_comp = entity.get_component(CombatComponent)
    # Process combat logic
```

### Persistence
```python
# Save component state
data = component.to_dict()

# Restore component state
component = ComponentClass.from_dict(data)
```

## Adding New Components

### 1. Define Component Class
```python
@dataclass
class MyComponent(BaseComponent):
    def __init__(self, param1: str, param2: int):
        super().__init__()
        self.param1 = param1
        self.param2 = param2
        self.computed_value = self._calculate_value()
    
    def _calculate_value(self):
        return self.param2 * 2
```

### 2. Add Properties for Computed Values
```python
@property
def effective_stat(self):
    """Calculate with modifiers from other components"""
    base = self.base_stat
    # Add logic to check other components
    return base
```

### 3. Implement Serialization
```python
def to_dict(self) -> Dict[str, Any]:
    base_dict = super().to_dict()
    base_dict.update({
        'param1': self.param1,
        'param2': self.param2
    })
    return base_dict

@classmethod
def from_dict(cls, data: Dict[str, Any]):
    component = cls(data['param1'], data['param2'])
    # Restore base component data
    component.entity_id = data.get('entity_id')
    return component
```

### 4. Create Corresponding System
```python
# In src/systems/
class MySystem(BaseSystem):
    def process(self, entities):
        for entity in entities.with_component(MyComponent):
            my_comp = entity.get_component(MyComponent)
            # Process component logic
```

## Component Dependencies

### Required Components
Some components may require others:
```python
class CombatComponent(BaseComponent):
    def __init__(self):
        super().__init__()
        # Requires UnitStatsComponent for damage calculation
```

### Optional Components
Components can enhance each other when present:
```python
@property
def total_defense(self):
    base = self.base_defense
    
    # Check for optional equipment component
    equipment = self.entity.get_component(EquipmentComponent)
    if equipment:
        base += equipment.get_defense_bonus()
    
    return base
```

## Testing Components

### Unit Tests
```python
def test_component_creation():
    comp = MyComponent("test", 5)
    assert comp.param1 == "test"
    assert comp.computed_value == 10

def test_component_serialization():
    comp = MyComponent("test", 5)
    data = comp.to_dict()
    restored = MyComponent.from_dict(data)
    assert restored.param1 == comp.param1
```

### Integration Tests
```python
def test_component_interaction():
    entity = Entity()
    stats = UnitStatsComponent("Test", UnitType.HEROMANCER)
    equipment = EquipmentComponent()
    
    entity.add_component(stats)
    entity.add_component(equipment)
    
    # Test cross-component calculations
    base_attack = stats.physical_attack
    # ... test equipment bonuses
```

## Best Practices

### Component Design
- Keep components focused on single responsibilities
- Avoid complex logic in components (use systems instead)
- Make components easily testable in isolation
- Document component dependencies clearly

### Performance
- Cache expensive calculations where appropriate
- Use properties for derived values
- Avoid deep component hierarchies
- Consider memory usage of component data

### Data Integrity
- Validate component data in constructors
- Provide sensible defaults for optional parameters
- Handle missing dependency components gracefully
- Implement robust serialization

### Organization
- Group related components in subdirectories
- Use consistent naming conventions
- Include comprehensive documentation
- Maintain backward compatibility for save files