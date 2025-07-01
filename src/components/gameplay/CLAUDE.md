# Gameplay Mechanics Components - Developer Guide

## Overview

This directory contains components that implement core gameplay mechanics for the Apex Tactics tactical RPG system. These components follow the Entity-Component-System (ECS) architecture and integrate with the asset management system.

## Architecture Pattern

### Component Structure
```python
@dataclass
class MyGameplayComponent(BaseComponent):
    def __init__(self, ...):
        super().__init__()
        # Component-specific initialization
    
    @property
    def computed_stat(self):
        """Properties for derived/computed values"""
        # Calculate based on base values + modifiers
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for save/load"""
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Deserialize from save data"""
```

## Adding a New Gameplay Mechanic

Follow this pattern when implementing new gameplay features:

### 1. Define the Component

Create a new file in `src/components/gameplay/` following the naming convention:
- `unit_stats.py` - Core unit attributes and combat stats
- `unit_type.py` - Unit type bonuses and classifications  
- `tactical_movement.py` - Movement and positioning mechanics
- `your_mechanic.py` - Your new mechanic

### 2. Asset Integration

If your mechanic uses data files:

1. **Create data structure** in `assets/data/your_category/`
2. **Update DataManager** in `src/core/assets/data_manager.py`:
   ```python
   @dataclass
   class YourMechanicData:
       # Define data structure
       
   def _load_your_mechanic(self):
       # Load from JSON files
   ```
3. **Reference assets** in your component:
   ```python
   from ...core.assets.data_manager import get_data_manager
   
   data_manager = get_data_manager()
   mechanic_data = data_manager.get_your_mechanic(id)
   ```

### 3. Stat Calculation Pattern

For mechanics that modify unit capabilities:

```python
@property
def effective_stat(self):
    """Calculate stat including all modifiers"""
    base_value = self.base_stat
    
    # Equipment modifiers
    if self.equipped_item and 'stats' in self.equipped_item:
        bonus = self.equipped_item['stats'].get('stat_bonus', 0)
        base_value += bonus
    
    # Other modifiers (buffs, debuffs, etc.)
    # ...
    
    return base_value
```

### 4. Equipment Integration Example

The weapon system demonstrates the complete pattern:

**Asset Data** (`assets/data/items/base_items.json`):
```json
{
  "id": "spear",
  "name": "Spear", 
  "type": "Weapons",
  "stats": {
    "physical_attack": 14,
    "attack_range": 2,
    "effect_area": 2
  }
}
```

**Component Implementation** (`unit_stats.py`):
```python
@property
def attack_range(self) -> int:
    """Get current attack range including weapon bonuses"""
    base_range = self.base_attack_range
    
    if self.equipped_weapon and 'stats' in self.equipped_weapon:
        weapon_range = self.equipped_weapon['stats'].get('attack_range', 0)
        return max(base_range, weapon_range)
    
    return base_range

def equip_weapon(self, weapon_data: Dict[str, Any]) -> bool:
    """Equip weapon and update stats"""
    if weapon_data.get('type') == 'Weapons':
        self.equipped_weapon = weapon_data
        return True
    return False
```

**Game Integration** (`apex-tactics.py`):
```python
def handle_attack(self, unit):
    """Use unit's current attack range from weapon"""
    range_tiles = unit.attack_range  # Automatically includes weapon bonus
    self.highlight_attack_range(unit)

def highlight_attack_effect_area(self, target_x, target_y):
    """Use unit's current effect area from weapon"""
    effect_radius = self.selected_unit.attack_effect_area
    # Highlight affected tiles...
```

## Component Types

### Core Gameplay Components

1. **UnitStatsComponent** - Attributes, HP/MP, combat calculations
2. **UnitTypeComponent** - Type bonuses and classifications
3. **TacticalMovementComponent** - Movement, positioning, pathfinding

### Equipment System Integration

All gameplay components can integrate with equipment:
- Use `@property` for computed stats
- Check `equipped_item['stats']` for bonuses
- Provide `equip_*()` methods for equipment changes

### Data-Driven Design

Components should be data-driven where possible:
- Load configuration from JSON files
- Use asset system for content
- Support hot-reloading for development

## Testing Pattern

For each new mechanic, create tests:

```python
def test_mechanic_basic():
    """Test basic functionality"""
    component = YourMechanicComponent(...)
    assert component.base_stat == expected_value

def test_mechanic_with_equipment():
    """Test with equipment modifiers"""
    component = YourMechanicComponent(...)
    equipment = {"stats": {"stat_bonus": 5}}
    component.equip_item(equipment)
    assert component.effective_stat == base_value + 5

def test_asset_integration():
    """Test loading from asset system"""
    # Test with real asset data
```

## Integration Checklist

When adding a new gameplay mechanic:

- [ ] Component follows BaseComponent pattern
- [ ] Asset data structure defined (if needed)
- [ ] DataManager integration (if needed)
- [ ] Properties for computed stats
- [ ] Equipment integration (if applicable)
- [ ] Serialization (to_dict/from_dict)
- [ ] Game controller integration
- [ ] UI display updates
- [ ] Testing coverage
- [ ] Documentation updates

## File Organization

```
src/components/gameplay/
├── __init__.py           # Component exports
├── unit_stats.py         # Core unit system
├── unit_type.py          # Type classifications
├── tactical_movement.py  # Movement mechanics
├── your_mechanic.py      # New mechanic
└── CLAUDE.md            # This documentation
```

## Common Patterns

### Modifier Stacking
```python
def calculate_with_modifiers(self, base_value, modifier_sources):
    """Apply modifiers from multiple sources"""
    total = base_value
    for source in modifier_sources:
        total += source.get('bonus', 0)
        total *= (1 + source.get('multiplier', 0))
    return total
```

### Conditional Effects
```python
def apply_conditional_bonus(self, base_value):
    """Apply bonuses based on conditions"""
    if self.meets_condition():
        return base_value + self.conditional_bonus
    return base_value
```

### Resource Management
```python
def consume_resource(self, amount):
    """Manage limited resources"""
    if self.current_resource >= amount:
        self.current_resource -= amount
        return True
    return False
```

## Example: Adding a Magic System

1. **Create** `magic_system.py` with spell casting mechanics
2. **Add** spell data in `assets/data/spells/base_spells.json`
3. **Update** DataManager with spell loading
4. **Integrate** with UnitStatsComponent for MP costs
5. **Add** spell targeting to tactical controller
6. **Update** UI to show spell information
7. **Test** complete spell casting workflow

This pattern ensures consistency across all gameplay mechanics and maintains the modular, data-driven architecture of the Apex Tactics system.