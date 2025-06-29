# Unit Data Assets

This directory contains centralized configuration data for all unit parameters in the tactical RPG system.

## File Structure

### `/units/unit_types.json`
Central configuration for all unit types including:
- Visual properties (colors, models, scales)
- Base stats (health, mana, movement, attack ranges)
- Attribute bonuses per unit type
- Combat parameters and resistances
- AI behavior preferences

### `/units/unit_generation.json`
Configuration for unit creation and stat generation:
- Base attribute ranges (min/max values)
- Random bonus ranges for type-specific attributes
- Derived stat calculation formulas
- Level scaling parameters

### `/units/ai_difficulty.json`
AI difficulty modifiers:
- Accuracy, damage, and health modifiers per difficulty
- Planning depth and mistake chances
- Aggression level modifications

## Data Manager

The `UnitDataManager` class in `/src/core/assets/unit_data_manager.py` provides a unified interface for accessing this data throughout the codebase.

### Usage Example

```python
from core.assets.unit_data_manager import get_unit_data_manager

# Get the global data manager instance
data_manager = get_unit_data_manager()

# Get unit color
color = data_manager.get_unit_color(UnitType.HEROMANCER)

# Get unit visual properties
visual_props = data_manager.get_unit_visual_properties(UnitType.MAGI)

# Get unit attribute bonuses
bonuses = data_manager.get_unit_attribute_bonuses(UnitType.WARGI)
```

## Files Updated

The following files were updated to use centralized data instead of hardcoded values:

1. **`/src/ui/visual/unit_renderer.py`** - Now loads colors and visual properties from data files
2. **`/src/ui/battlefield/unit_entity.py`** - Uses centralized visual properties
3. **`/src/components/gameplay/unit_stats.py`** - Uses data-driven stat generation and type bonuses
4. **`/src/ui/panels/control_panel.py`** - Gets unit colors from data manager

## Benefits

- **Centralized Configuration**: All unit parameters are defined in one place
- **Data-Driven Design**: Easy to modify unit properties without code changes
- **Consistency**: Ensures all systems use the same unit parameters
- **Maintainability**: Reduces code duplication and hardcoded values
- **Flexibility**: Easy to add new unit types or modify existing ones

## Adding New Unit Types

To add a new unit type:

1. Add the new enum value to `/src/core/models/unit_types.py`
2. Add the unit configuration to `/assets/data/units/unit_types.json`
3. The system will automatically load and use the new configuration

## Modifying Unit Parameters

Simply edit the JSON files in this directory. The changes will be automatically loaded when the game starts or the data manager is re-initialized.