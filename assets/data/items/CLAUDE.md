# Items Data Directory

## Overview

This directory contains JSON files defining all equipment, consumables, and materials in Apex Tactics. Items integrate with the equipment system to provide stat bonuses, special abilities, and gameplay effects.

## Current Files

### `base_items.json`
Core item set including:
- **4 Weapons**: Iron Sword, Steel Axe, Magic Bow, Spear
- **2 Armor pieces**: Leather Armor, Chain Mail  
- **1 Accessory**: Power Ring
- **2 Consumables**: Health Potion, Mana Potion
- **3 Materials**: Iron Ore, Magic Crystal, Dragon Scale

## Item Schema

### Required Fields
```json
{
  "id": "unique_identifier",
  "name": "Display Name",
  "type": "Weapons|Armor|Accessories|Consumables|Materials",
  "tier": "BASE|ENHANCED|ENCHANTED|SUPERPOWERED|METAPOWERED",
  "description": "Item description text",
  "stats": {},
  "requirements": {},
  "icon": "path/to/icon.png",
  "rarity": "common|uncommon|rare|epic|legendary",
  "value": 100,
  "stackable": true|false,
  "max_stack": 1
}
```

### Weapon-Specific Properties
```json
{
  "stats": {
    "physical_attack": 14,
    "magical_attack": 0,
    "attack_range": 2,      // Tiles unit can attack from
    "effect_area": 2,       // Area of effect radius
    "durability": 110,
    "weight": 2.8
  },
  "weapon_properties": {
    "reach": true,          // Long-range weapon
    "area_attack": true     // Hits multiple targets
  },
  "enchantments": ["never_miss", "magical_arrows"]
}
```

### Armor-Specific Properties
```json
{
  "stats": {
    "physical_defense": 15,
    "magical_defense": 3,
    "durability": 150,
    "weight": 8.5
  }
}
```

### Consumable Properties
```json
{
  "consumable": {
    "effect": "heal|restore_mana|buff|debuff",
    "amount": 50,
    "duration": 0           // 0 = instant, >0 = turns
  }
}
```

### Material Properties
```json
{
  "crafting_material": true,
  "legendary": true         // Special/rare materials
}
```

## Item Types

### Weapons
Combat equipment that affects attack capabilities:
- **Range Extension**: `attack_range` property extends melee reach
- **Area Effects**: `effect_area` creates splash damage zones
- **Damage Bonuses**: `physical_attack` and `magical_attack` boost damage
- **Special Properties**: Enchantments and weapon-specific traits

**Range/Area Examples:**
- **Sword**: Range 1, Area 0 (single target, adjacent)
- **Spear**: Range 2, Area 2 (reach 2 tiles, hits 2-tile radius)
- **Bow**: Range 3, Area 1 (long range, small splash)

### Armor
Defensive equipment that reduces incoming damage:
- **Physical Protection**: Reduces physical damage
- **Magical Resistance**: Reduces magical damage  
- **Durability**: How much use before breaking
- **Weight**: Affects movement and encumbrance

### Accessories
Special equipment providing unique bonuses:
- **Stat Boosts**: Direct attribute increases
- **Special Effects**: Unique gameplay modifiers
- **Set Bonuses**: Synergy with other equipment

### Consumables
Single-use items with immediate or temporary effects:
- **Healing Items**: Restore HP/MP
- **Buff Potions**: Temporary stat increases
- **Utility Items**: Special effects (teleport, etc.)
- **Stackable**: Multiple uses in single inventory slot

### Materials
Crafting components and trade goods:
- **Crafting Ingredients**: Used to create other items
- **Trade Goods**: High value for selling
- **Quest Items**: Special materials for story progression

## Weapon Range/Area System

The spear weapon demonstrates the range/area combat system:

```json
{
  "id": "spear",
  "stats": {
    "attack_range": 2,    // Can attack targets 2 tiles away
    "effect_area": 2      // Hits all targets within 2 tiles of target
  }
}
```

**Combat Integration:**
1. Unit selects attack action
2. Game highlights tiles within `attack_range`
3. Player selects target tile
4. All units within `effect_area` of target take damage
5. Visual effects show affected area

## Rarity System

Items use a standard rarity classification:
- **common** - Basic, easily found items
- **uncommon** - Improved quality, moderate rarity
- **rare** - High quality, limited availability
- **epic** - Exceptional items with special properties
- **legendary** - Unique, story-significant equipment

## Equipment Integration

Items work with the equipment system in components:

```python
# Loading item data
from src.core.assets.data_manager import get_data_manager
dm = get_data_manager()
spear_data = dm.get_item("spear")

# Equipping on units
unit.equip_weapon(spear_data.to_inventory_format())

# Dynamic stat calculation
attack_range = unit.attack_range  # Includes weapon bonus
```

## Adding New Items

1. **Design**: Plan item properties and role
2. **Add to JSON**: Follow schema in appropriate file
3. **Icon Asset**: Create/add icon graphic to assets/images/items/
4. **Test Loading**: Verify DataManager can load item
5. **Game Integration**: Test equipping and stat effects
6. **Balance**: Adjust values based on gameplay testing

## Best Practices

### Naming
- Use descriptive, immersive names
- Consistent terminology across related items
- Avoid generic numbering (Iron Sword vs Sword 1)

### Balance
- Consider item tier and expected character level
- Ensure meaningful progression between tiers
- Test combat effectiveness in actual gameplay

### Data Integrity
- All required fields must be present
- Icon paths should reference valid assets
- Requirements should match game systems

### Documentation
- Clear descriptions for player understanding
- Consistent formatting and terminology
- Update examples when adding new properties