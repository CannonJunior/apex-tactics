# Images Directory

## Overview

This directory contains all visual assets for Apex Tactics, organized by category and purpose. Images are loaded through the asset management system and support fallback textures for missing assets.

## Directory Structure

### `/icons/` - UI and Status Icons
General purpose icons for user interface elements:
- **Status Icons** - Health, mana, action point indicators
- **UI Elements** - Buttons, toggles, navigation arrows
- **Action Icons** - Move, attack, defend, spell symbols
- **Notification Icons** - Alerts, warnings, confirmations

**Recommended Specifications:**
- **Format**: PNG with transparency
- **Size**: 32x32, 64x64 for UI consistency
- **Style**: Consistent icon style across all UI elements

### `/items/` - Equipment and Inventory Graphics
Visual representations of all game items:

#### Subcategory Organization
```
items/
├── weapons/           # Swords, spears, bows, magical weapons
├── armor/            # Helmets, chest armor, boots, shields  
├── accessories/      # Rings, amulets, trinkets, jewelry
├── consumables/      # Potions, scrolls, food, temporary items
└── materials/        # Crafting components, trade goods, rare materials
```

**Asset Examples:**
- `weapons/iron_sword.png` - Basic melee weapon
- `weapons/spear.png` - Extended reach weapon with area effect
- `weapons/magic_bow.png` - Ranged weapon with magical properties
- `armor/leather_armor.png` - Light protective gear
- `armor/chain_mail.png` - Medium armor with good protection
- `accessories/power_ring.png` - Magical enhancement accessory

**Technical Specifications:**
- **Format**: PNG with alpha channel for transparency
- **Size**: 64x64 pixels for inventory grid consistency
- **Background**: Transparent for flexible UI placement
- **Style**: Isometric or top-down view for tactical feel

### `/tiles/` - Environment and Terrain
Battlefield and environment graphics:

#### Terrain Types
- **Ground Tiles** - Grass, stone, dirt, sand surfaces
- **Water Features** - Rivers, lakes, shallow/deep water
- **Obstacles** - Walls, rocks, trees, destructible objects
- **Special Terrain** - Magical areas, trap tiles, elevated surfaces

#### Interactive Elements
- **Highlighting** - Selection, movement range, attack area overlays
- **Status Effects** - Fire, ice, poison, magical enhancement areas
- **Damage Indicators** - Cracked terrain, battle damage effects

**Technical Specifications:**
- **Format**: PNG for complex tiles, consider tile sheets for performance
- **Size**: 64x64 pixels to match grid system
- **Tileable**: Edges should connect seamlessly with adjacent tiles
- **Variations**: Multiple versions of same terrain for visual variety

### `/ui/` - Interface Graphics
User interface components and backgrounds:

#### Panel Graphics
- **Backgrounds** - Panel borders, window frames, dialog boxes
- **Decorative Elements** - Corner ornaments, dividers, flourishes
- **Progress Bars** - Health, mana, experience, loading indicators
- **Frames** - Portrait frames, item slot borders, selection highlights

#### Interactive Elements
- **Buttons** - Normal, hover, pressed, disabled states
- **Sliders** - Volume controls, settings adjustments
- **Checkboxes** - Option selection, feature toggles
- **Tabs** - Panel navigation, category selection

**Technical Specifications:**
- **Format**: PNG with transparency for flexible layouts
- **Nine-Slice**: Use 9-slice sprites for scalable UI elements
- **State Variations**: Multiple versions for interactive feedback
- **Consistent Style**: Match overall game art direction

### `/units/` - Character and Unit Graphics
Visual representations of all game units:

#### Player Characters
- **Hero Types** - Different classes and specializations
- **Portraits** - Character faces for dialogue and UI
- **Equipment Variants** - Units showing different equipped items
- **Animation Frames** - Movement, attack, spell casting sequences

#### Enemy Units
- **Basic Enemies** - Common opponents with clear visual identity
- **Elite Units** - Special enemies with distinctive appearance
- **Bosses** - Unique, larger, more detailed enemy graphics
- **Faction Variants** - Different enemy types for various groups

#### Visual States
- **Health States** - Wounded, critically injured visual indicators
- **Status Effects** - Buffs, debuffs, special conditions
- **Equipment Display** - Show currently equipped weapons/armor
- **Facing Directions** - Multiple orientations for tactical positioning

**Technical Specifications:**
- **Format**: PNG with transparency for character cutouts
- **Size**: Variable based on unit size (64x64 for standard, larger for bosses)
- **Animation Ready**: Consider sprite sheets for animated units
- **Clear Silhouettes**: Distinct shapes for easy battlefield recognition

## Asset Creation Guidelines

### Art Style Consistency
- **Unified Palette** - Consistent color scheme across all assets
- **Lighting Direction** - Consistent light source for 3D appearance
- **Detail Level** - Appropriate detail for viewing distance and size
- **Fantasy Theme** - Maintain medieval fantasy aesthetic

### Technical Requirements
- **Transparency** - Use alpha channels for non-rectangular assets
- **Compression** - Balance file size with visual quality
- **Power of Two** - Prefer dimensions that are powers of 2 for GPU efficiency
- **Fallbacks** - Consider how assets look with missing texture fallbacks

### Naming Conventions
```
category_item_variant_state.png

Examples:
- weapons_iron_sword_base.png
- weapons_spear_enchanted.png
- armor_chain_mail_damaged.png
- units_hero_wounded.png
- tiles_grass_variant_01.png
```

## Asset Integration

### Loading Through Asset System
```python
# Load item icon for inventory display
item_icon = load_texture("items/weapons/spear.png", fallback="white_cube")

# Load with error handling
def load_item_texture(item_data):
    icon_path = item_data.get('icon', '')
    if icon_path:
        return load_texture(icon_path, fallback='items/default_item.png')
    
    # Type-based fallback
    type_defaults = {
        'Weapons': 'items/weapons/default_weapon.png',
        'Armor': 'items/armor/default_armor.png',
        'Accessories': 'items/accessories/default_accessory.png'
    }
    
    fallback_path = type_defaults.get(item_data.get('type'), 'white_cube')
    return load_texture(fallback_path, fallback='white_cube')
```

### UI Display Integration
```python
# Inventory item with texture
class InventoryItem(Draggable):
    def __init__(self, item_data, inventory_parent):
        # Load appropriate texture
        item_texture = self._load_item_texture()
        
        super().__init__(
            model='quad',
            texture=item_texture,
            color=color.gray if item_data.get('equipped_by') else color.white
        )
```

### Asset Validation
```python
def validate_asset_references():
    """Check that all referenced assets exist"""
    missing_assets = []
    
    # Check item icons
    for item in data_manager.get_all_items():
        icon_path = item.icon
        if not asset_loader.asset_exists('images', icon_path):
            missing_assets.append(f"Item icon: {icon_path}")
    
    # Check UI elements
    ui_assets = ['ui/button_normal.png', 'ui/panel_background.png']
    for asset in ui_assets:
        if not asset_loader.asset_exists('images', asset):
            missing_assets.append(f"UI asset: {asset}")
    
    return missing_assets
```

## Asset Workflow

### Creation Process
1. **Concept Design** - Sketch and plan visual appearance
2. **Asset Creation** - Create graphics in appropriate tools
3. **Technical Prep** - Optimize size, format, transparency
4. **Integration** - Add to appropriate directory with correct naming
5. **Testing** - Verify loading and display in game
6. **Optimization** - Adjust for performance and file size

### Version Control
- **Source Files** - Keep original high-resolution source files
- **Export Settings** - Document export parameters for consistency
- **Change Tracking** - Use git for asset version control
- **Backup Strategy** - Maintain backups of source materials

### Performance Optimization

#### File Size Management
```python
# Asset loading with size monitoring
def load_texture_with_monitoring(path, fallback=None):
    """Load texture with file size logging"""
    full_path = asset_loader.get_asset_path('images', path)
    
    if full_path.exists():
        file_size = full_path.stat().st_size
        if file_size > 1024 * 1024:  # 1MB warning
            print(f"⚠️ Large texture: {path} ({file_size // 1024}KB)")
        
        return load_texture(str(full_path))
    
    return load_texture(fallback) if fallback else None
```

#### Memory Management
- **Texture Atlasing** - Combine small textures into atlas sheets
- **Compression** - Use appropriate compression for texture types
- **Mip-mapping** - Generate multiple resolution levels for distance rendering
- **Streaming** - Load high-detail assets only when needed

## Asset Quality Standards

### Visual Quality
- **Resolution** - Appropriate detail for display size
- **Clarity** - Sharp, readable graphics at game scale
- **Consistency** - Matching style across all related assets
- **Polish** - Professional appearance with attention to detail

### Technical Quality
- **Optimization** - Balanced file size and visual quality
- **Format Compliance** - Correct file formats for intended use
- **Error Handling** - Graceful degradation with missing assets
- **Performance** - Efficient loading and rendering

### Asset Testing
```python
def test_asset_loading_performance():
    """Test asset loading speed and memory usage"""
    import time
    import psutil
    
    start_memory = psutil.virtual_memory().used
    start_time = time.time()
    
    # Load all game assets
    textures = []
    for item in data_manager.get_all_items():
        texture = load_texture(item.icon)
        textures.append(texture)
    
    end_time = time.time()
    end_memory = psutil.virtual_memory().used
    
    load_time = end_time - start_time
    memory_used = end_memory - start_memory
    
    print(f"Asset loading: {load_time:.2f}s, {memory_used // 1024 // 1024}MB")
    
    # Verify all textures loaded successfully
    assert all(texture is not None for texture in textures)
```

## Future Expansion

### Planned Asset Categories
- **Animations** - Character movement, spell effects, environmental
- **Particles** - Magical effects, damage indicators, environmental atmosphere
- **3D Models** - More detailed unit representations for close-up views
- **Cutscenes** - Story-related artwork and backgrounds

### Scalability Considerations
- **Resolution Independence** - Vector graphics for scalable UI elements
- **Platform Optimization** - Different asset sets for different devices
- **Localization** - Text-free graphics for international versions
- **Accessibility** - High contrast versions for visual accessibility

## Best Practices

### Organization
- **Logical Grouping** - Related assets in same directories
- **Clear Naming** - Descriptive, consistent file names
- **Documentation** - Record asset specifications and requirements
- **Dependencies** - Track which assets are used where

### Quality Control
- **Review Process** - Quality check for new and updated assets
- **Style Guide** - Document visual standards and requirements
- **Testing Integration** - Verify assets work correctly in game
- **Performance Monitoring** - Track asset loading and memory impact

### Maintenance
- **Regular Audits** - Check for unused or outdated assets
- **Format Updates** - Keep assets current with engine requirements
- **Optimization Reviews** - Periodically optimize file sizes and quality
- **Backup Procedures** - Maintain secure backups of all asset sources