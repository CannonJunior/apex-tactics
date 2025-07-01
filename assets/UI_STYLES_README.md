# UI Styles Configuration

This directory contains the `ui_styles.json` file which configures all visual styling for the Apex Tactics user interface.

## File Structure

### `ui_styles.json`
Central configuration file for all UI styling including colors, positions, and visual properties.

## Configuration Sections

### Health Bar (`bars.health_bar`)
- **color**: RGBA color values for the health bar fill
- **background_color**: RGBA color values for the health bar background
- **scale**: Width and height dimensions
- **position**: X,Y coordinates for positioning

### Resource Bars (`bars.resource_bars`)
Separate configurations for each resource type:

#### Rage Bar (`bars.resource_bars.rage`)
- **color**: Red (1.0, 0.0, 0.0, 1.0) for physical damage units
- **label**: "RAGE" text displayed next to bar

#### MP Bar (`bars.resource_bars.mp`)
- **color**: Blue (0.0, 0.0, 1.0, 1.0) for magical damage units  
- **label**: "MP" text displayed next to bar

#### Kwan Bar (`bars.resource_bars.kwan`)
- **color**: Yellow (1.0, 1.0, 0.0, 1.0) for spiritual damage units
- **label**: "KWAN" text displayed next to bar

### Labels (`labels.bar_labels`)
- **color**: White (1.0, 1.0, 1.0, 1.0) for all bar labels
- **scale**: Text size multiplier
- **offset_x**: Horizontal positioning offset from bars
- **origin**: Text alignment origin point

### Highlights (`highlights`)
Color configurations for different types of battlefield highlights:
- **movement**: Green highlighting for valid movement tiles
- **attack**: Red highlighting for attack range tiles
- **selection**: White highlighting for selected tiles
- **effect_area**: Yellow highlighting for area effect abilities

## Usage

### Accessing Styles in Code
```python
from ui.core.ui_style_manager import get_ui_style_manager

style_manager = get_ui_style_manager()

# Get health bar color
health_color = style_manager.get_health_bar_color()

# Get resource bar color by type
rage_color = style_manager.get_resource_bar_color("rage")
mp_color = style_manager.get_resource_bar_color("mp") 
kwan_color = style_manager.get_resource_bar_color("kwan")

# Get resource bar labels
rage_label = style_manager.get_resource_bar_label("rage")  # Returns "RAGE"
```

### Hot Reloading
Styles can be reloaded during development:
```python
from ui.core.ui_style_manager import reload_ui_styles

# Reload styles from file
reload_ui_styles()
```

## Color Format

All colors use RGBA format with values from 0.0 to 1.0:
```json
{
  "color": {
    "r": 1.0,    // Red component (0.0 - 1.0)
    "g": 0.0,    // Green component (0.0 - 1.0) 
    "b": 0.0,    // Blue component (0.0 - 1.0)
    "a": 1.0     // Alpha/transparency (0.0 = transparent, 1.0 = opaque)
  }
}
```

## Current Color Scheme

### Health Bar
- **Fill Color**: Green (0.0, 0.8, 0.0, 1.0)
- **Background**: Dark Gray (0.2, 0.2, 0.2, 1.0)

### Resource Bars
- **Rage**: Red (1.0, 0.0, 0.0, 1.0) - Used by Heromancer, Ubermensch
- **MP**: Blue (0.0, 0.0, 1.0, 1.0) - Used by Wargi, Magi  
- **Kwan**: Yellow (1.0, 1.0, 0.0, 1.0) - Used by Soul Linked, Realm Walker

### Labels
- **All Labels**: White (1.0, 1.0, 1.0, 1.0)

## Customization

To customize the UI appearance:

1. **Edit `assets/ui_styles.json`** with desired color values
2. **Save the file** - changes will be loaded automatically on next game launch
3. **Hot reload** during development using `reload_ui_styles()` function

### Example Customizations

#### Blue Health Bar
```json
"health_bar": {
  "color": {"r": 0.0, "g": 0.0, "b": 1.0, "a": 1.0}
}
```

#### Orange Rage Bar
```json
"rage": {
  "color": {"r": 1.0, "g": 0.5, "b": 0.0, "a": 1.0},
  "label": "FURY"
}
```

#### Purple Kwan Bar
```json
"kwan": {
  "color": {"r": 0.8, "g": 0.0, "b": 1.0, "a": 1.0},
  "label": "SPIRIT"
}
```

## Integration

The UI Style Manager integrates with:
- **TacticalRPGController** - Health and resource bar rendering
- **Highlight Systems** - Battlefield tile highlighting
- **UI Panels** - Future panel styling integration
- **Modal Dialogs** - Future modal styling support

## Future Extensions

Planned styling support:
- **Panel Backgrounds** - Inventory, character sheets, menus
- **Button Styles** - Action buttons, confirmation dialogs
- **Text Styles** - Different text types and hierarchies
- **Animation Styles** - Transition timings and effects
- **Theme Variants** - Light/dark mode, accessibility options