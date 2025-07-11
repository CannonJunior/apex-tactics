# UI Configuration Directory

## CRITICAL INSTRUCTION FOR CLAUDE

**⚠️ NEVER HARDCODE UI VALUES AGAIN ⚠️**

When creating or modifying ANY UI component (Entity, Button, Text, Panel, etc.), you MUST:

1. **USE MASTER UI CONFIG**: All visual properties (position, color, scale, model, texture) MUST come from `/assets/data/ui/master_ui_config.json`
2. **IMPORT UI CONFIG MANAGER**: Always use `from src.core.ui.ui_config_manager import get_ui_config_manager`
3. **ADD NEW VALUES TO MASTER CONFIG**: If you need a new UI property, add it to `master_ui_config.json` first
4. **NO HARDCODED VALUES**: Never use hardcoded positions like `(-0.4, 0.35)`, colors like `color.red`, or scales like `0.06`

## Master UI Configuration System

### Primary Configuration File
**`master_ui_config.json`** - Contains ALL UI configuration including:
- Positions, colors, scales for every UI component
- Color palettes for action types, UI states, health states
- Animation settings, tooltip configurations
- Modal dialog layouts and button configurations
- Theme variants and accessibility options

### Using the Configuration Manager

```python
# CORRECT - Use master UI config
from src.core.ui.ui_config_manager import get_ui_config_manager

ui_config = get_ui_config_manager()

# Get positions, colors, scales from config
position = ui_config.get_position_tuple('hotkey_system.slot_layout.start_position')
color = ui_config.get_color('colors.action_types.Attack')
scale = ui_config.get('hotkey_system.slot_layout.slot_size', 0.06)

# Create UI element using config values
Button(
    position=position,
    color=color,
    scale=scale,
    model=ui_config.get('models_and_textures.default_models.button', 'cube')
)
```

```python
# WRONG - Never do this
Button(
    position=(-0.4, 0.35, 0.0),  # ❌ HARDCODED
    color=color.red,             # ❌ HARDCODED  
    scale=0.06,                  # ❌ HARDCODED
    model='cube'                 # ❌ HARDCODED
)
```

### Adding New UI Components

When creating new UI components:

1. **Add configuration to master_ui_config.json:**
```json
{
  "my_new_panel": {
    "position": {"x": 0.5, "y": 0.0, "z": 0.0},
    "scale": {"x": 0.4, "y": 0.8, "z": 0.01},
    "color": "#1A1A26",
    "buttons": {
      "close_button": {
        "position": {"x": 0.35, "y": 0.35, "z": 0.01},
        "scale": 0.05,
        "color": "#CC0000"
      }
    }
  }
}
```

2. **Use configuration in code:**
```python
def create_my_panel(self):
    ui_config = get_ui_config_manager()
    
    panel_pos = ui_config.get_position_tuple('my_new_panel.position')
    panel_scale = ui_config.get_scale('my_new_panel.scale')
    panel_color = ui_config.get_color('my_new_panel.color')
    
    self.panel = Entity(
        parent=camera.ui,
        position=panel_pos,
        scale=(panel_scale['x'], panel_scale['y']),
        color=panel_color
    )
```

## Configuration Hierarchy

1. **`master_ui_config.json`** - Primary source for all UI settings
2. **Legacy configs** - Being phased out:
   - `layout_config.json` - Old layout configuration  
   - `unified_ui_config.json` - Old unified configuration
   - `character_interface_config.json` - Old character interface config

## Key Configuration Sections

- **`colors`** - All color palettes (action types, UI states, health states, tile highlights)
- **`battlefield`** - Grid tiles, units, lighting configuration
- **`camera`** - Camera controls and positioning modes
- **`panels`** - All UI panels (control, talent, character, inventory, party)
- **`ui_bars`** - Health, resource, action point bars
- **`hotkey_system`** - Hotkey slot layout and visual settings
- **`modals`** - Dialog boxes and confirmation modals
- **`tooltips`** - Tooltip styling and behavior
- **`animations`** - Animation timing and effects
- **`models_and_textures`** - Default 3D models and textures

## Coordinate System

- **X**: -1.0 (left) to 1.0 (right), 0.0 = center
- **Y**: -1.0 (bottom) to 1.0 (top), 0.0 = center  
- **Z**: -0.1 to 0.1, 0.0 = default depth

## Color System

All colors use hex format in configuration:
- Primary actions: `#FF0000` (Attack), `#0000FF` (Magic), `#FFFF00` (Spirit)
- UI states: `#FFFFFF` (normal), `#FFFF00` (selected), `#666666` (disabled)
- Health states: `#00FF00` (healthy), `#FFA500` (wounded), `#8B0000` (critical)

## Development Workflow

1. **Before coding**: Check if UI config exists in master config
2. **If missing**: Add configuration to `master_ui_config.json` first
3. **Use config manager**: Import and use `get_ui_config_manager()`
4. **Test changes**: Reload config with `reload_ui_config()` during development
5. **Validate**: Ensure no hardcoded values remain

## Legacy File Status

These files are being replaced by the master configuration:
- ✅ `layout_config.json` - Migrated to master config
- ✅ `unified_ui_config.json` - Migrated to master config  
- ✅ `character_interface_config.json` - Migrated to master config

## Emergency Fallbacks

The UI config manager provides fallback values if configuration is missing, but you should always add proper configuration rather than rely on fallbacks.

**Remember: Every UI element position, color, scale, model, and texture should come from the master UI configuration file!**