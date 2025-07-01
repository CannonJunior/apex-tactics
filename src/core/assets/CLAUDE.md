# Asset Management System

## Overview

The asset management system provides centralized loading, caching, and management of all game assets including data files, textures, audio, and animations. It ensures consistent asset access across the game and handles fallbacks gracefully.

## Architecture

### Core Components

#### `asset_loader.py` - AssetLoader Class
- **Purpose**: Low-level asset loading and caching
- **Capabilities**: JSON data, textures, audio files
- **Features**: Automatic fallbacks, error handling, performance caching

#### `data_manager.py` - DataManager Class  
- **Purpose**: High-level game data management
- **Capabilities**: Typed data access, inventory generation, data relationships
- **Features**: Hot reloading, structured data conversion, business logic

### System Architecture
```
Game Code
    ↓
DataManager (High-level, typed access)
    ↓
AssetLoader (Low-level, file loading)
    ↓
File System (JSON, PNG, WAV files)
```

## AssetLoader Features

### File Loading
```python
from src.core.assets.asset_loader import get_asset_loader

loader = get_asset_loader()

# Load JSON data with caching
data = loader.load_data("items/base_items.json")

# Load textures with fallbacks
texture = loader.load_texture("items/weapons/spear.png", fallback="white_cube")

# Load audio files
sound = loader.load_audio("sfx/attack.wav")
```

### Asset Types Supported
- **Data Files**: JSON format with UTF-8 encoding
- **Textures**: PNG, JPG via Ursina's load_texture
- **Audio**: WAV, OGG via Ursina's Audio system

### Caching System
- **Automatic**: Assets cached after first load
- **Performance**: Eliminates redundant file operations
- **Memory**: Intelligent cache management
- **Clearing**: Manual cache clearing for development

### Error Handling
- **Graceful Fallbacks**: Default assets when files missing
- **Logging**: Comprehensive error reporting
- **Validation**: File existence and format checking
- **Recovery**: Continues operation despite asset failures

## DataManager Features

### Typed Data Access
```python
from src.core.assets.data_manager import get_data_manager

dm = get_data_manager()

# Strongly typed item access
spear = dm.get_item("spear")  # Returns ItemData object
print(spear.name, spear.stats, spear.icon)

# Category-based queries
weapons = dm.get_items_by_type("Weapons")
all_items = dm.get_all_items()
```

### Data Classes

#### ItemData
Structured representation of game items:
```python
@dataclass
class ItemData:
    id: str
    name: str
    type: str
    tier: str
    description: str
    stats: Dict[str, Any]
    requirements: Dict[str, Any]
    icon: str
    rarity: str
    value: int
    stackable: bool
    max_stack: int
    # Optional fields...
```

#### AbilityData
Structured representation of abilities and spells:
```python
@dataclass
class AbilityData:
    id: str
    name: str
    type: str  # Physical, Magical, Spiritual
    tier: str
    description: str
    effects: Dict[str, Any]
    cost: Dict[str, int]  # AP, MP costs
    range: int
    area_of_effect: int
    cooldown: int
```

### Conversion Methods
```python
# Convert to formats used by other systems
inventory_format = item_data.to_inventory_format(
    equipped_by="Hero", 
    quantity=1
)

# Creates dict compatible with inventory system
```

### Sample Data Generation
```python
# Create sample inventory for testing/demos
sample_inventory = dm.create_sample_inventory({
    "iron_sword": "Hero",
    "spear": None,
    "health_potion": None
})
```

## Usage Patterns

### Game Initialization
```python
# Get singleton instances
asset_loader = get_asset_loader()
data_manager = get_data_manager()

# Data is automatically loaded on first access
```

### Component Integration
```python
# Equipment system usage
class UnitStatsComponent:
    def equip_weapon(self, weapon_data):
        if weapon_data.get('type') == 'Weapons':
            self.equipped_weapon = weapon_data
            # Stats automatically recalculated via properties
```

### UI Integration
```python
# Inventory panel usage
def _load_sample_data(self):
    if ASSETS_AVAILABLE:
        self.sample_items = create_sample_inventory()
    else:
        self._load_fallback_data()
```

## Configuration

### Asset Directory Structure
```
assets/
├── data/           # JSON data files
├── images/         # Textures and graphics
├── audio/          # Sound effects and music
└── animations/     # Animation data
```

### Default Paths
- **Assets Root**: `project_root/assets/`
- **Data Files**: `assets/data/`
- **Images**: `assets/images/`
- **Audio**: `assets/audio/`

## Development Features

### Hot Reloading
```python
# Reload all data from files (development)
data_manager.reload_data()

# Clear specific cache types
asset_loader.clear_cache('data')  # or 'texture', 'audio', 'all'
```

### Asset Listing
```python
# List all assets of a type
data_files = asset_loader.list_assets('data')
image_files = asset_loader.list_assets('images')
audio_files = asset_loader.list_assets('audio')
```

### Path Utilities
```python
# Get full paths to assets
item_path = asset_loader.get_asset_path('data', 'items/base_items.json')
texture_path = asset_loader.get_asset_path('images', 'items/spear.png')

# Check asset existence
if asset_loader.asset_exists('images', 'items/new_weapon.png'):
    # Load the asset
```

## Error Recovery

### Missing Files
- **Data**: Returns None, logs warning
- **Textures**: Uses fallback texture, logs warning  
- **Audio**: Returns None, logs warning

### Corrupt Data
- **JSON**: Catches decode errors, returns None
- **Validation**: Checks required fields where possible

### Fallback Strategy
1. **Primary**: Try to load requested asset
2. **Fallback**: Use specified fallback asset
3. **Default**: Use system default (e.g., 'white_cube')
4. **None**: Return None if all else fails

## Performance Considerations

### Caching
- **Memory Usage**: Monitor cache size in production
- **Cache Clearing**: Clear during scene transitions if needed
- **Lazy Loading**: Assets loaded only when requested

### Asset Optimization
- **File Sizes**: Keep individual assets reasonably sized
- **Formats**: Use appropriate formats for asset types
- **Compression**: Balance quality vs. file size

## Best Practices

### Asset Organization
- Follow directory conventions consistently
- Use descriptive filenames
- Group related assets logically

### Error Handling
- Always check for None returns
- Provide meaningful fallbacks
- Log asset loading issues for debugging

### Performance
- Preload critical assets when possible
- Clear caches during major scene transitions
- Monitor memory usage with large asset sets

### Development
- Use hot reloading for rapid iteration
- Test with missing assets to verify fallbacks
- Validate asset references during build process