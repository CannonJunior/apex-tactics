# Game Data Directory

## Overview

This directory contains JSON-based data files that define all game content for Apex Tactics. These files are loaded by the DataManager and provide the structured data that drives gameplay mechanics.

## Data Categories

### `items/` - Equipment and Inventory
Defines all items that can be equipped, used, or collected:
- **Weapons** - Attack damage, range, special properties
- **Armor** - Defense values, resistances, durability
- **Accessories** - Rings, amulets with stat bonuses
- **Consumables** - Potions, scrolls with temporary effects
- **Materials** - Crafting components and trade goods

**Example Structure (`base_items.json`):**
```json
{
  "version": "1.0",
  "items": [
    {
      "id": "spear",
      "name": "Spear",
      "type": "Weapons",
      "tier": "BASE",
      "stats": {
        "physical_attack": 14,
        "attack_range": 2,
        "effect_area": 2
      },
      "requirements": {"level": 2, "strength": 10},
      "icon": "items/weapons/spear.png",
      "rarity": "common",
      "value": 75,
      "stackable": false
    }
  ]
}
```

### `abilities/` - Skills and Spells
Defines special abilities, spells, and skills:
- **Combat Abilities** - Attack skills and special moves
- **Magic Spells** - Offensive and defensive magic
- **Passive Skills** - Permanent character enhancements
- **Utility Powers** - Non-combat abilities

**Schema:**
```json
{
  "id": "fireball",
  "name": "Fireball",
  "type": "Magical",
  "tier": "ENHANCED",
  "effects": {"damage": 25, "burn": 3},
  "cost": {"mp": 15, "ap": 2},
  "range": 4,
  "area_of_effect": 2,
  "cooldown": 3
}
```

### `characters/` - Character Definitions
Defines player characters and notable NPCs:
- **Player Characters** - Starting stats, background, growth
- **Important NPCs** - Story characters with unique traits
- **Character Templates** - Base templates for character creation

### `units/` - Combat Unit Types
Defines the characteristics of different unit types:
- **Unit Templates** - Base stats for each unit type
- **AI Behaviors** - Combat AI patterns and preferences
- **Special Abilities** - Unit-specific powers and traits

### `zones/` - Maps and Environments
Defines battle arenas, maps, and environmental data:
- **Battle Maps** - Grid layouts, terrain types, objectives
- **Environmental Effects** - Weather, hazards, special conditions
- **Interactive Objects** - Destructible terrain, switches, etc.

## Data Format Standards

### Required Fields
All data files must include:
- `version` - Data format version for compatibility
- Primary array (e.g., `items`, `abilities`, `characters`)

### Common Properties
Most game objects share these properties:
- `id` - Unique identifier (snake_case)
- `name` - Display name for UI
- `type` - Category classification
- `tier` - Power/quality level (BASE, ENHANCED, ENCHANTED, etc.)
- `description` - Flavor text or tooltip description
- `icon` - Path to associated image asset

### Stat System Integration
Data integrates with the 9-attribute system:
- **Physical** - `strength`, `fortitude`, `finesse`
- **Mental** - `wisdom`, `wonder`, `spirit`  
- **Social** - `faith`, `worthy`, `speed`

### Tier System
Standard progression tiers:
1. **BASE** - Starting/common quality
2. **ENHANCED** - Improved/uncommon quality
3. **ENCHANTED** - Magical/rare quality
4. **SUPERPOWERED** - Exceptional/epic quality
5. **METAPOWERED** - Legendary/mythic quality

## Loading and Access

### DataManager Integration
```python
from src.core.assets.data_manager import get_data_manager

dm = get_data_manager()

# Get specific items
spear = dm.get_item("spear")
health_potion = dm.get_item("health_potion")

# Get by category
all_weapons = dm.get_items_by_type("Weapons")
consumables = dm.get_items_by_type("Consumables")

# Create sample inventory
inventory = dm.create_sample_inventory()
```

### Hot Reloading
Data can be reloaded during development:
```python
dm.reload_data()  # Refreshes all data from files
```

## File Naming Conventions

- Use descriptive names: `base_items.json`, `player_spells.json`
- Category prefixes: `weapons_medieval.json`, `armor_magical.json`
- Version suffixes for iterations: `spells_v2.json`

## Schema Validation

### Required Properties
Each object type has required fields that must be present.

### Data Types
- **Numbers** - Integers for discrete values, floats for percentages
- **Strings** - UTF-8 text for names and descriptions
- **Booleans** - True/false flags
- **Objects** - Nested data structures for complex properties
- **Arrays** - Lists of related items

### Validation Tools
Consider using JSON Schema validators to ensure data integrity.

## Best Practices

### Organization
- Group related items in same file when logical
- Split large categories into multiple themed files
- Use consistent naming and structure patterns

### Documentation
- Include version numbers in data files
- Add comments where JSON format allows
- Document special properties and their effects

### Performance
- Avoid overly deep nesting (max 3-4 levels)
- Keep individual files under 1MB when possible
- Use arrays efficiently for bulk data

### Maintenance
- Regular validation of data integrity
- Test all data references are valid
- Update version numbers when schemas change

## Development Workflow

1. **Design**: Plan data structure and properties
2. **Create**: Write JSON following established patterns  
3. **Validate**: Ensure proper format and required fields
4. **Test**: Load through DataManager in development
5. **Integrate**: Reference from game code
6. **Version**: Commit to source control