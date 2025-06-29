# Apex Tactics Modularization Plan

## Overview

This plan details the complete replacement of the monolithic `apex-tactics.py` system with the modular ECS architecture built in this project, while preserving the CameraController.

## Current State Analysis

### Monolithic System (apex-tactics.py)
- **8 classes** in 957 lines of code
- **Direct coupling** between all systems
- **Mixed concerns** (data, logic, presentation)
- **Hard to test** individual components
- **Limited extensibility** due to tight coupling

### ECS Architecture (alt-apex-tactics)
- **Component-based** entity management
- **Event-driven** system communication
- **Modular** systems with single responsibilities
- **Performance optimized** with caching and pooling
- **Portable** UI framework for multi-engine support

## Migration Strategy

### Phase 1: Core Entity Conversion
Replace monolithic classes with ECS entities:

```
apex-tactics.py               → alt-apex-tactics ECS
================               ===================
Unit                          → Entity + Components:
  - UnitType enum            →   • UnitTypeComponent
  - 9 attributes             →   • AttributeStats
  - Combat stats             →   • AttackComponent, DefenseComponent
  - Movement                 →   • MovementComponent
  - Position                 →   • Transform

BattleGrid                    → TacticalGrid + EntityManager
TurnManager                   → Existing TurnManager + BattleManager
```

### Phase 2: System Replacement
Replace monolithic systems with modular ones:

```
apex-tactics.py Systems       → alt-apex-tactics Systems
=======================       =========================
TacticalRPG (main controller) → World + BattleManager
Input handling               → InteractionManager
Visual management            → GridVisualizer + CombatAnimator
Modal dialogs                → UI Framework
Combat resolution            → CombatSystem
```

### Phase 3: Preserved Systems
Keep working systems from apex-tactics.py:

```
Preserved from apex-tactics.py
==============================
CameraController             → Direct integration (no changes)
  - Orbit/Free/Top-down modes
  - Mouse and keyboard controls
  - Grid-centric positioning
```

## Detailed Component Mapping

### 1. Unit → Entity + Components

#### UnitTypeComponent
```python
@dataclass
class UnitTypeComponent(BaseComponent):
    unit_type: UnitType
    type_bonuses: Dict[str, int]
```

#### Existing AttributeStats (Enhanced)
- Already implements 9-attribute system
- Performance optimized (<1ms calculations)
- Derived stat caching
- **Enhancement needed**: Unit type bonuses integration

#### Movement Integration
```python
# Existing MovementComponent + new TacticalMovement
@dataclass
class TacticalMovementComponent(BaseComponent):
    movement_points: int
    current_movement_points: int
    movement_range: int
```

### 2. BattleGrid → TacticalGrid + Spatial System

#### Existing TacticalGrid (Enhanced)
- Already implements grid-based positioning
- Pathfinding integration
- **Enhancement needed**: Unit placement management

#### Spatial Indexing System
```python
class SpatialSystem(BaseSystem):
    def update(self, delta_time: float, entities: EntityManager):
        # Manage entity positions on grid
        # Handle movement validation
        # Update spatial indices
```

### 3. Visual System → Component-Based Rendering

#### Visual Components
```python
@dataclass
class VisualComponent(BaseComponent):
    model: str
    color: Color
    scale: Vector3
    visible: bool

@dataclass
class GridTileComponent(BaseComponent):
    grid_position: Vector2Int
    highlighted: bool
    highlight_color: Color
```

#### Rendering System
```python
class RenderingSystem(BaseSystem):
    def update(self, delta_time: float, entities: EntityManager):
        # Update Ursina entities from components
        # Handle visibility changes
        # Manage visual effects
```

## Implementation Plan

### Step 1: Create New Demo Framework
```python
# New file: src/demos/modular_apex_tactics_demo.py
class ModularApexTacticsDemo:
    def __init__(self):
        self.world = World()
        self.battle_manager = BattleManager(self.world)
        self.camera_controller = CameraController()  # From apex-tactics.py
        self.interaction_manager = InteractionManager()
        
    def create_tactical_units(self):
        # Convert apex-tactics Units to ECS entities
        
    def setup_battle_environment(self):
        # Create grid, lighting, visual elements
        
    def run_demo(self):
        # Main game loop
```

### Step 2: Unit Conversion System
```python
class UnitConverter:
    @staticmethod
    def apex_unit_to_entity(apex_unit: Unit, world: World) -> Entity:
        entity = world.entity_manager.create_entity()
        
        # Convert attributes
        entity.add_component(AttributeStats(
            strength=apex_unit.strength,
            fortitude=apex_unit.fortitude,
            # ... all 9 attributes
        ))
        
        # Add unit type
        entity.add_component(UnitTypeComponent(apex_unit.type))
        
        # Add position
        entity.add_component(Transform(Vector3(apex_unit.x, 0, apex_unit.y)))
        
        # Add combat components
        entity.add_component(AttackComponent(attack_range=apex_unit.attack_range))
        entity.add_component(DefenseComponent())
        
        # Add movement
        entity.add_component(MovementComponent(
            movement_range=apex_unit.move_points
        ))
        
        return entity
```

### Step 3: Combat System Integration
```python
class TacticalCombatSystem(BaseSystem):
    def __init__(self):
        self.combat_system = CombatSystem()  # Existing system
        
    def update(self, delta_time: float, entities: EntityManager):
        # Process combat using existing CombatSystem
        # Apply damage to AttributeStats components
        # Handle death and destruction
```

### Step 4: Input and Interaction
```python
class TacticalInputSystem(BaseSystem):
    def __init__(self, camera_controller: CameraController):
        self.camera_controller = camera_controller
        self.interaction_manager = InteractionManager()
        
    def handle_input(self, key: str):
        # Camera controls go to CameraController
        self.camera_controller.handle_input(key)
        
        # Game controls go to InteractionManager
        self.interaction_manager.handle_input(key)
```

## New Demo Features

### Enhanced Capabilities
1. **Modular Design**: Each system can be tested and modified independently
2. **Performance Monitoring**: Built-in profiling and statistics
3. **Event-Driven Architecture**: Systems communicate through events
4. **Component Inspection**: Real-time component debugging
5. **Save/Load System**: Entity serialization capabilities

### Preserved Functionality
1. **Camera System**: Exact same camera controls as apex-tactics.py
2. **Unit Types**: All 6 unit types with type-specific bonuses
3. **9-Attribute System**: Comprehensive stat calculations
4. **Turn-Based Combat**: Strategic turn management
5. **Grid Tactics**: 8x8 tactical grid positioning

### New Demonstrations
1. **ECS Performance**: Show component query performance
2. **System Modularity**: Enable/disable individual systems
3. **Event Monitoring**: Visualize system communication
4. **Component Editor**: Live editing of entity components
5. **Battle Analytics**: Combat statistics and metrics

## File Structure

```
src/demos/
├── modular_apex_tactics_demo.py     # Main demo application
├── unit_converter.py                # Unit → Entity conversion
├── tactical_systems.py              # Tactical-specific systems
└── demo_ui.py                       # Demo-specific UI components

src/components/
├── gameplay/
│   ├── unit_type.py                 # UnitTypeComponent
│   ├── tactical_movement.py         # TacticalMovementComponent
│   └── battle_state.py             # Battle-specific components

src/systems/
├── spatial_system.py               # Grid-based positioning
├── tactical_combat_system.py       # Combat integration
├── rendering_system.py             # Visual management
└── tactical_input_system.py        # Input handling
```

## Success Metrics

### Performance Targets
- **Entity Creation**: <10ms for full army
- **Turn Processing**: <50ms per turn
- **Visual Updates**: 60fps with 50+ units
- **Memory Usage**: <100MB for complete battle

### Functionality Goals
- **100% Feature Parity**: All apex-tactics.py features working
- **Enhanced Modularity**: Systems independently testable
- **Better Performance**: Faster than monolithic version
- **Improved UX**: Better visual feedback and controls

## Testing Strategy

### Unit Tests
- Component serialization/deserialization
- System update logic
- Entity conversion accuracy
- Combat calculation correctness

### Integration Tests
- Full battle simulation
- Camera integration
- UI system interaction
- Performance benchmarks

### User Acceptance
- Side-by-side comparison with apex-tactics.py
- Feature completeness verification
- Performance measurement
- User experience evaluation

This plan provides a complete roadmap for converting the monolithic apex-tactics.py into a modern, modular ECS architecture while preserving all functionality and improving extensibility.