# Assets Directory

## Overview

This directory contains all game assets for Apex Tactics, organized by type and purpose. Assets are loaded dynamically by the asset management system and support hot-reloading during development.

## Directory Structure

### `/data/` - Game Data Files
JSON-based data files defining game content:
- **`items/`** - Equipment, consumables, materials
- **`abilities/`** - Spells, skills, special attacks
- **`characters/`** - Character definitions and stats
- **`units/`** - Unit types and configurations
- **`zones/`** - Maps, levels, battle arenas

### `/images/` - Visual Assets
Graphics and textures for game rendering:
- **`items/`** - Equipment and inventory icons
- **`units/`** - Character sprites and animations
- **`tiles/`** - Environment and terrain graphics  
- **`ui/`** - Interface elements and buttons
- **`icons/`** - General UI and status icons

### `/audio/` - Sound Assets
Audio files for gameplay:
- **`sfx/`** - Sound effects for actions and events
- **`music/`** - Background music and themes

### `/animations/` - Animation Data
Animation sequences and timing data for visual effects.

## Asset Loading

Assets are loaded through the centralized asset management system:

```python
from src.core.assets.asset_loader import load_data, load_texture, load_audio

# Load game data
item_data = load_data("items/base_items.json")

# Load textures with fallbacks
texture = load_texture("items/weapons/spear.png", fallback="white_cube")

# Load audio
sound = load_audio("sfx/attack.wav")
```

## File Formats

### Data Files (.json)
- UTF-8 encoded JSON
- Schema validation recommended
- Support for versioning

### Images (.png recommended)
- PNG format preferred for transparency
- Power-of-2 dimensions when possible
- Consistent naming conventions

### Audio (.wav, .ogg)
- WAV for high-quality short sounds
- OGG for compressed longer tracks

## Naming Conventions

### Files
- `snake_case` for filenames
- Descriptive names: `iron_sword.png` not `sword1.png`
- Version suffixes: `spell_v2.json`

### Directories
- Lowercase, plural nouns
- Logical grouping by game system

## Development Workflow

1. **Add Asset**: Place file in appropriate directory
2. **Reference**: Use relative path from asset type root
3. **Test**: Verify loading through asset system
4. **Version**: Use git for version control

## Asset Organization

### Items
```
items/
├── weapons/           # Weapon graphics and data
├── armor/            # Armor sets and pieces  
├── accessories/      # Rings, amulets, trinkets
├── consumables/      # Potions, scrolls, food
└── materials/        # Crafting components
```

### Characters
```
characters/
├── player/           # Player character data
├── npcs/            # Non-player characters
└── enemies/         # Enemy unit definitions
```

### Environment
```
tiles/
├── terrain/         # Ground, water, walls
├── objects/         # Interactive objects
└── effects/         # Visual effect overlays
```

## Performance Considerations

- **Caching**: Assets are cached after first load
- **Lazy Loading**: Assets loaded on-demand
- **Fallbacks**: Default assets prevent crashes
- **Optimization**: Compress large assets appropriately

## Asset Pipeline

1. **Creation**: Create/edit assets in appropriate tools
2. **Processing**: Optimize for game engine
3. **Integration**: Place in correct directory structure
4. **Testing**: Verify in-game appearance/function
5. **Deployment**: Include in distribution builds

## Best Practices

- Keep asset sizes reasonable for performance
- Use consistent art style across related assets
- Include fallback/placeholder assets
- Document special requirements in asset metadata
- Test asset loading failure scenarios
- Version control all assets