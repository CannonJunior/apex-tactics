# UI Panels Directory

## Overview

This directory contains the user interface panel system for Apex Tactics. Panels provide modular, interactive UI components that display game information and allow player interaction with various game systems.

## Panel Architecture

### Base Panel System
All panels inherit from `BasePanel` which provides:
- **Visibility Management** - Show/hide functionality
- **Ursina Integration** - Rendering and input handling
- **Content Updates** - Dynamic data refreshing
- **Lifecycle Management** - Setup and cleanup

```python
class BasePanel:
    def __init__(self):
        self.is_visible = False
        
    def toggle_visibility(self):
        """Show/hide panel"""
        
    def update_content(self, data: Dict[str, Any]):
        """Update panel with new data"""
        
    def cleanup(self):
        """Clean up panel resources"""
```

### Panel System Features
- **Modular Design** - Independent, reusable components
- **Asset Integration** - Uses asset system for data
- **Interactive Elements** - Buttons, tabs, drag-and-drop
- **Responsive Layout** - Adapts to different screen sizes

## Panel Types

### Core Panels

#### `character_panel.py` - Character Information
Displays detailed character stats and information:
- **Attributes Display** - Show 9-attribute system values
- **Combat Stats** - Attack, defense, HP/MP values
- **Equipment Summary** - Currently equipped items
- **Status Effects** - Active buffs/debuffs

**Key Features:**
```python
class CharacterPanel(BasePanel):
    def update_character_info(self, character: Entity):
        """Update display with character data"""
        
    def show_attribute_breakdown(self, attribute: str):
        """Show detailed attribute calculation"""
```

#### `inventory_panel.py` - Item Management
Interactive inventory with drag-and-drop functionality:
- **Grid Layout** - Visual item organization
- **Item Categories** - Tabbed interface by item type
- **Drag-and-Drop** - Interactive item management
- **Equipment Integration** - Equip/unequip items
- **Asset Integration** - Loads items from data system

**Key Features:**
```python
class InventoryPanel(BasePanel):
    def _populate_items(self):
        """Load items from asset system"""
        
    def _handle_item_drop(self, item, position):
        """Process item movement in grid"""
        
    def switch_tab(self, category: str):
        """Filter items by category"""
```

#### `party_panel.py` - Party Management
Displays and manages party members:
- **Party Overview** - All party members at a glance
- **Member Selection** - Click to view detailed stats
- **Formation Management** - Arrange party positions
- **Status Monitoring** - Health and status overview

#### `talent_panel.py` - Abilities and Skills
Manages character abilities and skill progression:
- **Ability Trees** - Visual skill progression
- **Spell Management** - Active abilities and cooldowns
- **Skill Points** - Available points for upgrades
- **Prerequisites** - Show ability requirements

#### `upgrade_panel.py` - Character Enhancement
Handles character progression and upgrades:
- **Level Progression** - Experience and level ups
- **Attribute Increases** - Stat point allocation
- **Equipment Upgrades** - Item enhancement options
- **Advancement Paths** - Future progression preview

### Management Panels

#### `control_panel.py` - Game Controls
Central game control interface:
- **Action Buttons** - Move, Attack, Defend, etc.
- **Unit Information** - Current unit stats display
- **Turn Management** - End turn, game flow controls
- **Camera Controls** - View mode switching

#### `game_panel_manager.py` - Panel Coordination
Manages all panels and their interactions:
- **Panel Registration** - Track all active panels
- **Visibility Management** - Coordinate panel display
- **Input Routing** - Direct inputs to appropriate panels
- **State Synchronization** - Keep panels updated

```python
class GamePanelManager:
    def __init__(self):
        self.panels = {}
        self.active_panels = set()
        
    def register_panel(self, name: str, panel: BasePanel):
        """Add panel to management system"""
        
    def show_panel(self, name: str):
        """Display specific panel"""
        
    def update_all_panels(self, game_state: Dict):
        """Update all active panels with new data"""
```

## Panel Implementation Patterns

### Asset Integration
```python
class InventoryPanel(BasePanel):
    def _load_sample_data(self):
        """Load items from asset system"""
        if ASSETS_AVAILABLE:
            try:
                self.sample_items = create_sample_inventory()
                print(f"✅ Loaded {len(self.sample_items)} items from asset files")
            except Exception as e:
                print(f"⚠️ Failed to load from assets: {e}, using fallback data")
                self._load_fallback_data()
        else:
            self._load_fallback_data()
```

### Interactive Elements
```python
class InventoryItem(Draggable):
    def __init__(self, item_data: Dict[str, Any], inventory_parent, **kwargs):
        # Create draggable item with tooltip
        self.tooltip = Tooltip(f"{item_data['name']} [{item_data['tier']}]")
        
    def drag(self):
        """Called when item starts being dragged"""
        self.org_pos = (self.x, self.y)
        
    def drop(self):
        """Called when item is dropped"""
        # Snap to grid and handle swapping
        self.x = round(self.x, 3)
        self.y = round(self.y, 3)
```

### Data Updates
```python
def update_content(self, data: Dict[str, Any]):
    """Update panel with new data"""
    if 'inventory' in data:
        self.sample_items = data['inventory']
        # Refresh inventory display
        self._refresh_inventory_display()
        self._update_info_panel()
```

## Panel Features

### Tabbed Interface
Many panels use tabbed organization:
```python
def _create_tab_buttons(self):
    """Create tab buttons for filtering content"""
    tabs = ["All", "Weapons", "Armor", "Accessories", "Consumables", "Materials"]
    
    for i, tab in enumerate(tabs):
        btn = Button(
            text=tab,
            color=color.azure if tab == self.current_tab else color.dark_gray,
            position=(-0.4 + i * 0.09, 0.45),
            on_click=lambda t=tab: self.switch_tab(t)
        )
        self.tab_buttons.append(btn)
```

### Tooltips and Help
Panels provide contextual information:
```python
# Item tooltips
tooltip_text = f"{item_name} [{tier}]{quantity_info}{equipped_info}"
self.tooltip = Tooltip(tooltip_text)
self.tooltip.background.color = color.hsv(0, 0, 0, .8)

# Help text
help_text = [
    "Interactive Inventory",
    "Drag items to rearrange", 
    "Equipped items shown in gray"
]
```

### Visual Feedback
Panels provide clear visual state indicators:
```python
# Equipment status
item_color = color.gray if self.is_equipped else color.white

# Button states
btn.color = color.azure if active else color.dark_gray

# Highlight effects
tile.highlight(color.yellow)
```

## Panel Lifecycle

### Initialization
```python
def __init__(self, game_reference: Optional[Any] = None):
    """Initialize panel with game context"""
    if not URSINA_AVAILABLE:
        raise ImportError("Ursina is required for UI panels")
    
    self.game_reference = game_reference
    self._is_visible = False
    
    # Load data and create UI elements
    self._load_sample_data()
    self._create_ui_elements()
```

### Visibility Management
```python
def toggle_visibility(self):
    """Toggle panel visibility"""
    self._is_visible = not self._is_visible
    
    # Toggle all UI elements
    for element in self.ui_elements:
        element.enabled = self._is_visible
    
    status = "shown" if self._is_visible else "hidden"
    print(f"Panel {status}")
```

### Cleanup
```python
def cleanup(self):
    """Clean up panel resources"""
    for element in self.ui_elements:
        destroy(element)
    self.ui_elements.clear()
```

## Input Handling

### Keyboard Shortcuts
```python
def handle_keyboard_input(self, key: str):
    """Handle panel-specific keyboard shortcuts"""
    if key == 'i':  # Toggle inventory
        self.toggle_visibility()
    elif key == 'tab' and self._is_visible:
        self.cycle_tabs()
```

### Mouse Interactions
```python
def handle_mouse_input(self, event: MouseEvent):
    """Handle mouse interactions with panel elements"""
    if event.type == 'click':
        self.handle_click(event.position)
    elif event.type == 'drag':
        self.handle_drag(event.start, event.end)
```

## Panel Communication

### Event System
```python
# Panels communicate through events
def on_item_equipped(self, item_data: Dict):
    """Handle item equipment event"""
    self.update_equipment_display(item_data)
    self.game_reference.update_unit_stats()

# Panel manager broadcasts events
def broadcast_event(self, event_type: str, data: Dict):
    """Send event to all relevant panels"""
    for panel in self.active_panels:
        if hasattr(panel, f'on_{event_type}'):
            getattr(panel, f'on_{event_type}')(data)
```

### Data Synchronization
```python
def synchronize_panels(self):
    """Keep all panels in sync with game state"""
    game_state = self.get_current_game_state()
    
    for panel_name, panel in self.panels.items():
        if panel.is_visible():
            panel.update_content(game_state)
```

## Adding New Panels

### 1. Create Panel Class
```python
class MyNewPanel(BasePanel):
    def __init__(self, game_reference=None):
        super().__init__(game_reference)
        self._create_ui_elements()
    
    def _create_ui_elements(self):
        """Create panel-specific UI"""
        # Implementation here
        
    def update_content(self, data: Dict[str, Any]):
        """Update with new data"""
        # Implementation here
```

### 2. Register with Manager
```python
# In game initialization
panel_manager.register_panel('my_panel', MyNewPanel(game))
```

### 3. Add Input Handling
```python
# In input handler
if key == 'm':  # Toggle my panel
    panel_manager.toggle_panel('my_panel')
```

## Best Practices

### Design Principles
- **Consistency** - Use consistent UI patterns across panels
- **Clarity** - Clear visual hierarchy and information presentation
- **Responsiveness** - Provide immediate feedback for interactions
- **Accessibility** - Support keyboard navigation and tooltips

### Performance
- **Lazy Loading** - Create UI elements only when needed
- **Efficient Updates** - Update only changed elements
- **Resource Management** - Clean up unused UI elements
- **Caching** - Cache frequently displayed data

### User Experience
- **Discoverability** - Make panel functions obvious
- **Forgiveness** - Allow undo/cancel for destructive actions
- **Feedback** - Provide clear success/error messages
- **Help** - Include tooltips and contextual help

### Integration
- **Modular Design** - Keep panels independent where possible
- **Clean APIs** - Well-defined interfaces between panels and game
- **Event Driven** - Use events for loose coupling
- **Testing** - Unit test panel logic and integration points