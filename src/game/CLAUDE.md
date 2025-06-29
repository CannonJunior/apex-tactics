# Game Logic Directory

## Overview

This directory contains the high-level game logic and controllers that orchestrate the tactical RPG experience. It bridges the gap between low-level ECS systems and the user interface, managing game flow, turn progression, and player interactions.

## Architecture

### Game Layer Responsibilities
- **Game Flow Management** - Turn progression, battle phases, win conditions
- **Controller Logic** - Player input handling and game state transitions
- **Battle Orchestration** - Coordinate systems for tactical combat
- **Legacy Integration** - Bridge between new ECS and existing apex-tactics.py code

### Component Organization
```
src/game/
├── battle/          # Battle management and turn system
├── controllers/     # Main game controllers
├── factories/       # Entity and object creation
├── legacy/         # Wrapper for existing apex-tactics.py integration
├── progression/    # Character and game progression (planned)
└── story/          # Story and campaign management (planned)
```

## Battle Management (`/battle/`)

### Core Battle Components

#### `battle_manager.py` - Battle Orchestration
Central coordinator for tactical battles:
- **Battle Initialization** - Setup battlefield, units, objectives
- **State Management** - Track battle state and progression
- **Victory Conditions** - Monitor win/loss conditions
- **Battle Events** - Coordinate between systems and UI

```python
class BattleManager:
    def __init__(self, battle_config: BattleConfig):
        """Initialize battle with configuration"""
        
    def start_battle(self):
        """Begin tactical battle sequence"""
        
    def process_turn(self, actions: List[Action]):
        """Process player/AI actions for current turn"""
        
    def check_victory_conditions(self) -> Optional[BattleResult]:
        """Check if battle has ended"""
```

#### `turn_manager.py` - Turn Order and Progression
Manages turn-based gameplay flow:
- **Initiative Order** - Determine turn sequence based on speed
- **Turn Phases** - Movement, action, reaction phases
- **Time Management** - Action point and resource management
- **Turn Events** - Beginning/end of turn processing

```python
class TurnManager:
    def advance_turn(self):
        """Move to next unit in turn order"""
        
    def get_current_unit(self) -> Entity:
        """Get unit whose turn it is"""
        
    def can_perform_action(self, unit: Entity, action: Action) -> bool:
        """Check if unit can perform action"""
```

#### `action_queue.py` - Action Processing
Manages and processes player and AI actions:
- **Action Validation** - Ensure actions are legal
- **Action Sequencing** - Order simultaneous actions
- **Animation Coordination** - Sync actions with visual effects
- **Interrupt Handling** - Manage reactions and counter-actions

## Controllers (`/controllers/`)

### `tactical_rpg_controller.py` - Main Game Controller
Central controller extracted from apex-tactics.py for better modularity:

#### Core Responsibilities
- **Game State Management** - Overall game state and transitions
- **Input Handling** - Process player inputs and UI interactions
- **System Coordination** - Bridge between ECS systems and game logic
- **UI Integration** - Connect game logic with user interface

#### Key Features
```python
class TacticalRPGController:
    def __init__(self):
        """Initialize game controller with ECS world"""
        self.world = World()
        self.battle_manager = BattleManager()
        self.turn_manager = TurnManager()
        
    def handle_player_input(self, input_event: InputEvent):
        """Process player actions and update game state"""
        
    def update_game_state(self, delta_time: float):
        """Update all game systems each frame"""
        
    def handle_tile_click(self, x: int, y: int):
        """Process tactical grid interactions"""
```

#### Integration Points
- **ECS Integration** - Manages entities, components, and systems
- **UI Bridge** - Connects game logic with interface panels
- **Asset Integration** - Uses asset system for game content
- **Legacy Bridge** - Interfaces with existing apex-tactics.py code

## Factories (`/factories/`)

### `unit_factory.py` - Entity Creation
Centralized creation of game entities with proper component setup:

#### Factory Responsibilities
- **Unit Creation** - Create units with appropriate components
- **Component Configuration** - Set up component relationships
- **Asset Integration** - Load unit data from asset system
- **Template Management** - Reusable unit templates

```python
class UnitFactory:
    def create_unit(self, unit_type: UnitType, position: Vector3) -> Entity:
        """Create unit entity with all required components"""
        
    def create_player_unit(self, character_data: dict) -> Entity:
        """Create player-controlled unit"""
        
    def create_ai_unit(self, ai_config: dict) -> Entity:
        """Create AI-controlled unit"""
```

#### Component Assembly
```python
def create_combat_unit(self, unit_data: dict) -> Entity:
    """Create fully equipped combat unit"""
    entity = Entity()
    
    # Core components
    entity.add_component(UnitStatsComponent(unit_data))
    entity.add_component(MovementComponent(unit_data))
    entity.add_component(CombatComponent(unit_data))
    
    # Optional components based on unit type
    if unit_data.get('has_equipment'):
        entity.add_component(EquipmentComponent())
    
    if unit_data.get('ai_controlled'):
        entity.add_component(AIControllerComponent(unit_data['ai_type']))
    
    return entity
```

## Legacy Integration (`/legacy/`)

### Bridging ECS and apex-tactics.py
Wrapper classes that allow gradual migration from monolithic to ECS architecture:

#### `unit_wrapper.py` - Unit System Bridge
```python
class UnitWrapper:
    """Wrapper to make ECS units compatible with apex-tactics.py"""
    def __init__(self, entity: Entity):
        self.entity = entity
        self.stats = entity.get_component(UnitStatsComponent)
    
    @property
    def attack_range(self) -> int:
        """Expose ECS unit stats as legacy properties"""
        return self.stats.attack_range
```

#### `battle_grid_wrapper.py` - Grid System Bridge
```python
class BattleGridWrapper:
    """Make ECS spatial system compatible with legacy grid"""
    def move_unit(self, unit: UnitWrapper, x: int, y: int) -> bool:
        """Bridge legacy grid movement to ECS systems"""
```

#### `turn_manager_wrapper.py` - Turn System Bridge
```python
class TurnManagerWrapper:
    """Bridge ECS turn system with legacy turn management"""
    def next_turn(self):
        """Integrate new turn system with existing UI"""
```

## Game Flow Management

### Battle Flow
```
Battle Start
├── Initialize Battlefield
├── Create Units (via Factory)
├── Set Victory Conditions
└── Begin Turn Loop
    ├── Determine Turn Order
    ├── Process Player/AI Actions
    ├── Update Game State (via Systems)
    ├── Check Victory Conditions
    └── Advance Turn
```

### Controller Flow
```
Input Event
├── Input Validation
├── Game State Check
├── Action Creation
├── System Processing
├── UI Updates
└── Event Broadcasting
```

## Integration Patterns

### ECS to UI Bridge
```python
class GameController:
    def update_ui_from_ecs(self):
        """Update UI panels with current ECS state"""
        current_unit = self.turn_manager.get_current_unit()
        if current_unit:
            stats = current_unit.get_component(UnitStatsComponent)
            self.ui_manager.update_unit_panel(stats.to_dict())
```

### Asset to Component Bridge
```python
def create_unit_from_asset(self, unit_id: str) -> Entity:
    """Create unit entity from asset data"""
    unit_data = self.data_manager.get_unit(unit_id)
    entity = self.unit_factory.create_unit(unit_data)
    
    # Equip default weapon if specified
    if unit_data.default_weapon:
        weapon = self.data_manager.get_item(unit_data.default_weapon)
        equipment = entity.get_component(EquipmentComponent)
        equipment.equip_weapon(weapon)
    
    return entity
```

### Legacy Compatibility
```python
def handle_legacy_attack(self, legacy_unit, target_x: int, target_y: int):
    """Handle attack from legacy UI using ECS systems"""
    # Convert legacy unit to ECS entity
    entity = self.legacy_mapper.get_entity(legacy_unit)
    
    # Use ECS combat system
    combat_system = self.world.get_system(CombatSystem)
    result = combat_system.execute_attack(entity, target_x, target_y)
    
    # Update legacy UI
    self.legacy_ui.update_attack_result(result)
```

## Future Expansion

### Planned Directories

#### `/progression/` - Character Progression
- **Experience System** - Level ups and skill progression
- **Ability Trees** - Unlock new abilities and specializations
- **Equipment Progression** - Item upgrades and enchantments

#### `/story/` - Campaign Management
- **Story Events** - Cutscenes and narrative sequences
- **Mission Structure** - Campaign progression and objectives
- **Save System** - Game state persistence

### Migration Strategy
1. **Phase 1**: Legacy wrappers maintain compatibility
2. **Phase 2**: Gradual replacement of legacy systems
3. **Phase 3**: Full ECS implementation with legacy removal

## Testing Game Logic

### Controller Testing
```python
def test_battle_initialization():
    controller = TacticalRPGController()
    battle_config = create_test_battle()
    
    controller.start_battle(battle_config)
    
    assert controller.battle_manager.is_battle_active()
    assert len(controller.get_active_units()) > 0
```

### Integration Testing
```python
def test_attack_flow():
    controller = TacticalRPGController()
    attacker = controller.create_test_unit("spear_warrior")
    defender = controller.create_test_unit("armored_soldier")
    
    # Simulate attack input
    attack_event = AttackInputEvent(attacker, defender.position)
    controller.handle_player_input(attack_event)
    
    # Verify results
    assert defender.hp < defender.max_hp
    assert controller.battle_manager.get_last_action_result().success
```

## Best Practices

### Separation of Concerns
- **Controllers** - Handle input and coordinate systems
- **Managers** - Manage specific game aspects (battles, turns)
- **Factories** - Create and configure entities
- **Wrappers** - Provide compatibility layers

### State Management
- Use ECS world as single source of truth
- Minimize state duplication between systems
- Emit events for state changes
- Provide clear state transition APIs

### Error Handling
- Validate all inputs at controller level
- Provide graceful degradation for missing components
- Log important game events for debugging
- Handle edge cases in battle logic

### Performance
- Cache frequently accessed entities and components
- Use efficient algorithms for turn order calculation
- Minimize object creation during gameplay
- Profile controller performance regularly