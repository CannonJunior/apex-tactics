# Code Examples and Patterns

This document contains proven code patterns and examples from the tactical RPG engine implementation.

## ECS Patterns

### Basic Entity Creation
```python
# Standard entity creation with components
entity = EntityManager.create_entity()
entity.add_component(Transform(position=Vector3(0, 0, 0)))
entity.add_component(Stats(strength=10, fortitude=10))
entity.add_component(Combat())
```

### Component Registration Pattern
```python
# Register component with system
class ExampleComponent(BaseComponent):
    def __init__(self):
        super().__init__()
        self.value = 0
    
    def update(self, delta_time: float):
        pass

# Register with component registry
ComponentRegistry.register(ExampleComponent)
```

### System Update Pattern
```python
# Standard system update loop
class ExampleSystem(BaseSystem):
    def update(self, delta_time: float, entities: List[Entity]):
        for entity in entities:
            if entity.has_component(ExampleComponent):
                component = entity.get_component(ExampleComponent)
                self._process_component(component, delta_time)
```

## Stat Calculation Patterns

### Nine-Attribute System Creation
```python
# Create entity with nine-attribute stats
from src.components.stats.attributes import AttributeStats
from src.components.stats.resources import ResourceManager
from src.components.stats.modifiers import ModifierManager

entity = world.create_entity(
    Transform(position=Vector3(0, 0, 0)),
    AttributeStats(strength=15, fortitude=12, finesse=14, 
                  wisdom=10, wonder=8, worthy=11,
                  faith=9, spirit=10, speed=13),
    ResourceManager(max_mp=120, max_rage=100, base_kwan=50),
    ModifierManager()
)
```

### Derived Stat Calculation with Caching
```python
# High-performance derived stat calculation
@property
def derived_stats(self) -> Dict[str, int]:
    # Use cache if valid and recent (within 100ms)
    if (self._cache_valid and 
        time.time() - self._cache_timestamp < 0.1):
        return self._derived_cache.copy()
    
    # Recalculate with complex formulas
    self._derived_cache = {
        'hp': self.fortitude * 10 + self.strength * 2,
        'mp': self.wisdom * 8 + self.wonder * 3,
        'physical_attack': int(self.strength * 1.5 + self.finesse * 0.5),
        'initiative': int(self.speed * 0.8 + self.worthy * 1.0 + self.finesse * 0.4)
    }
    
    self._cache_timestamp = time.time()
    self._cache_valid = True
    return self._derived_cache.copy()
```

### Resource System Usage
```python
# Three-resource system with different behaviors
resources = entity.get_component(ResourceManager)

# MP regenerates over time
resources.mp.update(delta_time)

# Rage builds from damage and decays
resources.rage.add_from_damage_taken(damage_amount)
resources.rage.update(delta_time)  # Natural decay

# Kwan changes based on location
resources.kwan.update_for_location("temple", {"blessed": 0.2})

# Check resource costs
if resources.can_afford_cost(mp_cost=30, rage_cost=50):
    resources.spend_resources(mp_cost=30, rage_cost=50)
```

### Advanced Modifier System
```python
# Create temporary modifiers with stacking rules
strength_buff = Modifier(
    stat_name="strength",
    modifier_type=ModifierType.FLAT,
    value=5,
    source=ModifierSource.SPELL,
    source_id="strength_spell",
    duration=30.0,  # 30 seconds
    stacking_rule=StackingRule.LIMITED,
    stack_limit=3
)

modifier_manager = entity.get_component(ModifierManager)
modifier_manager.add_modifier(strength_buff)

# Calculate final stat with modifiers
final_strength = modifier_manager.calculate_final_stat(base_strength, "strength")
```

## Grid System Patterns

### Tactical Grid Creation and Setup
```python
# Create tactical grid with height variations
from src.core.math.grid import TacticalGrid, TerrainType
from src.core.math.pathfinding import AStarPathfinder

grid = TacticalGrid(width=10, height=10, cell_size=1.0)

# Set up terrain with height variations
grid.set_cell_height(Vector2Int(3, 3), 2.0)  # Elevated position
grid.set_cell_terrain(Vector2Int(5, 5), TerrainType.DIFFICULT)
grid.set_cell_terrain(Vector2Int(2, 7), TerrainType.WALL)

# Generate procedural height map
grid.generate_height_map(seed=42, roughness=0.5)
```

### High-Performance Pathfinding
```python
# A* pathfinding with <2ms target performance
pathfinder = AStarPathfinder(grid)

start = Vector2Int(0, 0)
goal = Vector2Int(9, 9)

result = pathfinder.find_path(start, goal, max_cost=20.0)

if result.success:
    print(f"Path found: {len(result.path)} steps")
    print(f"Search time: {result.search_time*1000:.2f}ms")
    print(f"Nodes explored: {result.nodes_explored}")
else:
    print("No path found")

# Get reachable positions within movement range
reachable = pathfinder.find_reachable_positions(start, max_movement=5.0)
```

### Grid Position Conversion with Height
```python
# Convert between world and grid coordinates
def world_to_grid(world_pos: Vector3) -> Vector2Int:
    return Vector2Int(
        int(world_pos.x / grid.cell_size),
        int(world_pos.z / grid.cell_size)
    )

def grid_to_world(grid_pos: Vector2Int) -> Vector3:
    cell = grid.get_cell(grid_pos)
    height = cell.height if cell else 0.0
    return Vector3(
        (grid_pos.x + 0.5) * grid.cell_size,
        height,
        (grid_pos.y + 0.5) * grid.cell_size
    )
```

### Line of Sight and Tactical Queries
```python
# Check line of sight with height consideration
has_los = grid.get_line_of_sight(
    from_pos=Vector2Int(1, 1),
    to_pos=Vector2Int(8, 8)
)

# Get cells in attack range
attack_range = grid.get_cells_in_range(
    center=Vector2Int(5, 5),
    range_distance=3
)

# Calculate movement cost with height penalties
movement_cost = grid.get_movement_cost(
    from_pos=Vector2Int(2, 2),
    to_pos=Vector2Int(3, 3)  # Might be uphill
)
```

## MCP Server Patterns

### Tool Registration
```python
# Register MCP tool for tactical analysis
@mcp.tool
def analyze_tactical_situation(unit_id: str) -> Dict[str, Any]:
    """Analyze tactical situation for AI decision making"""
    unit = get_unit(unit_id)
    return {
        "position_value": calculate_position_value(unit),
        "threat_level": assess_threats(unit),
        "opportunities": find_opportunities(unit)
    }
```

### Resource Definition
```python
# Define MCP resource for game state
@mcp.resource("tactical_state")
def get_tactical_state() -> str:
    """Get current tactical battle state"""
    return json.dumps({
        "units": [unit.to_dict() for unit in active_units],
        "turn_order": current_turn_order,
        "battlefield": battlefield.to_dict()
    })
```

## Performance Patterns

### Component Pooling
```python
# Object pooling for frequently created/destroyed components
class ComponentPool:
    def __init__(self, component_type: Type, initial_size: int = 100):
        self.pool = [component_type() for _ in range(initial_size)]
        self.available = list(self.pool)
    
    def get(self):
        if self.available:
            return self.available.pop()
        else:
            return self.component_type()
    
    def release(self, component):
        component.reset()
        self.available.append(component)
```

### Lazy Loading Pattern
```python
# Lazy load expensive resources
class LazyResource:
    def __init__(self, loader_func):
        self._loader = loader_func
        self._resource = None
    
    @property
    def resource(self):
        if self._resource is None:
            self._resource = self._loader()
        return self._resource
```

Additional patterns will be added as the implementation progresses.