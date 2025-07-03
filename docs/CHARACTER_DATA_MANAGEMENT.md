# Character Data Management System

## Overview

This document outlines the character data management system for Apex Tactics, designed to bridge the gap between static character definitions in `assets/data/characters/all_characters.json` and dynamic runtime character state during gameplay.

## Architecture

### Data Flow
```
Character Assets (JSON) → Character Templates → Runtime Character Instances → UI Panels
```

### Core Components

#### 1. Character Templates (Static Data)
- **Source**: `assets/data/characters/all_characters.json`
- **Purpose**: Define base character properties, starting equipment, talents, abilities
- **Managed by**: `UnitDataManager`
- **Scope**: Immutable game design data

#### 2. Character Instances (Runtime Data)
- **Source**: Created from Character Templates
- **Purpose**: Track dynamic character state during gameplay
- **Managed by**: `CharacterStateManager` (new component)
- **Scope**: Mutable game state data

#### 3. Active Character Registry
- **Source**: Tracks currently selected/active characters
- **Purpose**: Provide UI panels with current character context
- **Managed by**: `TacticalRPGController` + `CharacterStateManager`
- **Scope**: UI state management

## System Design

### CharacterStateManager Class

```python
class CharacterStateManager:
    """
    Manages runtime character state and bridges asset data with game state.
    
    Responsibilities:
    - Create character instances from templates
    - Track character state changes during gameplay
    - Provide character data to UI panels
    - Manage inventory, talents, and ability state
    """
    
    def __init__(self, unit_data_manager: UnitDataManager):
        self.unit_data_manager = unit_data_manager
        self.character_instances: Dict[str, CharacterInstance] = {}
        self.active_character_id: Optional[str] = None
        
    def create_character_instance(self, unit_type: UnitType, instance_id: str) -> CharacterInstance:
        """Create runtime character from template data"""
        
    def get_active_character(self) -> Optional[CharacterInstance]:
        """Get currently active character for UI display"""
        
    def set_active_character(self, instance_id: str):
        """Set active character and notify UI panels"""
        
    def update_character_state(self, instance_id: str, updates: Dict[str, Any]):
        """Update character state and notify observers"""
```

### CharacterInstance Class

```python
@dataclass
class CharacterInstance:
    """
    Runtime instance of a character with dynamic state.
    
    Combines template data with runtime modifications.
    """
    # Identity
    instance_id: str
    unit_type: UnitType
    
    # Base character data (from template)
    template_data: Dict[str, Any]
    
    # Runtime state
    current_stats: Dict[str, int]
    current_inventory: List[Dict[str, Any]]
    unlocked_talents: Set[str]
    equipped_items: Dict[str, Any]
    status_effects: List[Dict[str, Any]]
    
    # Game progression
    experience: int = 0
    level: int = 1
    skill_points: int = 0
    
    # Battle state
    current_hp: int = 0
    current_mp: int = 0
    current_rage: int = 0
    current_kwan: int = 0
    position: Optional[Tuple[int, int]] = None
    
    def get_effective_stats(self) -> Dict[str, int]:
        """Calculate final stats including equipment and status effects"""
        
    def get_inventory_items(self) -> List[Dict[str, Any]]:
        """Get current inventory with equipped status"""
        
    def get_available_abilities(self) -> List[Dict[str, Any]]:
        """Get currently available hotkey abilities"""
        
    def unlock_talent(self, talent_id: str) -> bool:
        """Unlock a talent if requirements are met"""
        
    def equip_item(self, item_id: str, slot: str) -> bool:
        """Equip an item to a slot"""
```

## Integration Points

### 1. Unit Creation Integration

```python
# In tactical_rpg_controller.py
def create_unit_from_character_data(self, unit_type: UnitType, x: int, y: int) -> Unit:
    """Create Unit instance enhanced with character data"""
    
    # Get character template data
    character_template = self.unit_data_manager.get_unit_data(unit_type)
    
    # Create character instance
    instance_id = f"{unit_type.value}_{x}_{y}_{uuid.uuid4().hex[:8]}"
    character_instance = self.character_state_manager.create_character_instance(
        unit_type, instance_id
    )
    
    # Create Unit with enhanced data
    unit = Unit(
        name=character_template.get('display_name', unit_type.value.title()),
        unit_type=unit_type,
        x=x, y=y,
        # Initialize with character template stats
        **character_template.get('stats', {})
    )
    
    # Store character instance reference
    unit.character_instance_id = instance_id
    
    # Apply starting equipment
    self._apply_starting_equipment(unit, character_instance)
    
    return unit
```

### 2. Character Panel Integration

```python
# Enhanced character_panel.py
class CharacterPanel:
    def __init__(self, character_state_manager: CharacterStateManager):
        self.character_state_manager = character_state_manager
        # ... existing init code
        
    def update_from_active_character(self):
        """Update panel with active character data"""
        active_character = self.character_state_manager.get_active_character()
        if active_character:
            self._update_character_display(active_character)
            self._update_inventory_display(active_character)
            self._update_talents_display(active_character)
            self._update_abilities_display(active_character)
    
    def _update_character_display(self, character: CharacterInstance):
        """Update basic character info section"""
        self.character_name_text.text = f"Name: {character.template_data['display_name']}"
        self.character_class_text.text = f"Class: {character.unit_type.value.title()}"
        self.character_level_text.text = f"Level: {character.level}"
        
        # Update stats with effective values (including equipment bonuses)
        effective_stats = character.get_effective_stats()
        self.strength_text.text = f"STR: {effective_stats['strength']}"
        # ... update other stats
        
    def _update_inventory_display(self, character: CharacterInstance):
        """Update inventory section with character's current items"""
        inventory_items = character.get_inventory_items()
        # Display starting items and equipped status
        
    def _update_talents_display(self, character: CharacterInstance):
        """Update talents section with unlocked talents"""
        talents = character.template_data.get('talents', {})
        unlocked = character.unlocked_talents
        # Display talent tree with unlock status
        
    def _update_abilities_display(self, character: CharacterInstance):
        """Update abilities section with available hotkey abilities"""
        abilities = character.get_available_abilities()
        # Display hotkey bindings and cooldowns
```

### 3. Game Controller Integration

```python
# In tactical_rpg_controller.py
class TacticalRPG:
    def __init__(self):
        # ... existing init
        self.character_state_manager = CharacterStateManager(self.unit_data_manager)
        
    def select_unit(self, unit: Unit):
        """Enhanced unit selection with character state management"""
        self.active_unit = unit
        
        # Update active character in state manager
        if hasattr(unit, 'character_instance_id'):
            self.character_state_manager.set_active_character(unit.character_instance_id)
        
        # Notify UI panels
        self._notify_character_selection_changed()
        
    def _notify_character_selection_changed(self):
        """Notify all UI panels that character selection changed"""
        if hasattr(self, 'character_panel'):
            self.character_panel.update_from_active_character()
        if hasattr(self, 'inventory_panel'):
            self.inventory_panel.update_from_active_character()
        # ... notify other panels
```

## Data Synchronization

### Event-Driven Updates

```python
class CharacterStateManager:
    def __init__(self):
        self.observers: List[callable] = []
        
    def add_observer(self, callback: callable):
        """Add observer for character state changes"""
        self.observers.append(callback)
        
    def _notify_observers(self, event_type: str, character_id: str, data: Any):
        """Notify all observers of character state changes"""
        for observer in self.observers:
            observer(event_type, character_id, data)
            
    def update_character_state(self, instance_id: str, updates: Dict[str, Any]):
        """Update character state and notify observers"""
        if instance_id in self.character_instances:
            character = self.character_instances[instance_id]
            
            # Apply updates
            for key, value in updates.items():
                if key == 'inventory':
                    character.current_inventory = value
                elif key == 'stats':
                    character.current_stats.update(value)
                # ... handle other update types
                
            # Notify observers
            self._notify_observers('character_updated', instance_id, updates)
```

### UI Panel Registration

```python
# In game initialization
character_state_manager.add_observer(character_panel.on_character_state_changed)
character_state_manager.add_observer(inventory_panel.on_character_state_changed)
character_state_manager.add_observer(talent_panel.on_character_state_changed)

# In panels
def on_character_state_changed(self, event_type: str, character_id: str, data: Any):
    """Handle character state change events"""
    if event_type == 'character_updated' and character_id == self.current_character_id:
        self.update_display()
    elif event_type == 'active_character_changed':
        self.current_character_id = character_id
        self.update_from_active_character()
```

## State Persistence

### Save/Load System

```python
class CharacterStateManager:
    def save_character_states(self) -> Dict[str, Any]:
        """Serialize character states for save system"""
        return {
            'characters': {
                instance_id: {
                    'instance_id': char.instance_id,
                    'unit_type': char.unit_type.value,
                    'current_stats': char.current_stats,
                    'current_inventory': char.current_inventory,
                    'unlocked_talents': list(char.unlocked_talents),
                    'equipped_items': char.equipped_items,
                    'experience': char.experience,
                    'level': char.level,
                    # ... other persistent data
                }
                for instance_id, char in self.character_instances.items()
            },
            'active_character_id': self.active_character_id
        }
        
    def load_character_states(self, data: Dict[str, Any]):
        """Restore character states from save data"""
        for instance_id, char_data in data['characters'].items():
            # Recreate character instance from saved data
            character = self._restore_character_instance(char_data)
            self.character_instances[instance_id] = character
            
        self.active_character_id = data.get('active_character_id')
```

## Performance Considerations

### Lazy Loading
- Character instances created only when units are spawned
- Template data cached in UnitDataManager
- UI updates triggered only for active character

### Memory Management
- Character instances cleaned up when units are destroyed
- Observer cleanup when panels are destroyed
- Minimal data duplication between template and instance

### Update Efficiency
- Only affected UI panels receive notifications
- Batch updates for multiple stat changes
- Differential updates for inventory changes

## Migration Strategy

### Phase 1: Core System Implementation
1. Implement CharacterStateManager and CharacterInstance
2. Create character instances from existing Unit creation
3. Basic integration with character panel

### Phase 2: UI Integration
1. Update all UI panels to use character state data
2. Implement observer pattern for real-time updates
3. Enhanced character panel with full character data

### Phase 3: Advanced Features
1. Save/load system integration
2. Character progression and talent unlocking
3. Equipment effects and stat calculations

## Usage Examples

### Creating a Character
```python
# Game initialization
unit_type = UnitType.HEROMANCER
instance_id = character_state_manager.create_character_instance(unit_type, "hero_001")

# Character now has:
# - All template data from all_characters.json
# - Starting inventory items
# - Unlocked starting talents
# - Initial stats and resources
```

### UI Panel Updates
```python
# When player selects a unit
controller.select_unit(unit)

# Automatically triggers:
# 1. character_state_manager.set_active_character(unit.character_instance_id)
# 2. character_panel.update_from_active_character()
# 3. All other panels receive character change notification
```

### Character Progression
```python
# When character gains experience
character_state_manager.update_character_state("hero_001", {
    'experience': character.experience + 100,
    'level': character.level + 1,
    'skill_points': character.skill_points + 3
})

# UI panels automatically update to show new values
```

This system provides a clean separation between static character designs and dynamic gameplay state while maintaining real-time UI synchronization and efficient resource usage.