# Core Engine Systems

<system_context>
Fundamental engine systems providing ECS architecture, event handling, mathematical utilities, and core infrastructure.
</system_context>

<critical_notes>
- ECS must be implemented first as foundation for all other systems
- Event system provides decoupled communication between systems
- Math utilities must be optimized for performance (<1ms stat calculations)
- Core systems have no dependencies on game-specific logic
</critical_notes>

<file_map>
ECS architecture: @src/core/ecs/
Event system: @src/core/events/
Math utilities: @src/core/math/
Core utilities: @src/core/utils/
</file_map>

<paved_path>
1. Implement ECS (Entity, Component, System base classes)
2. Create event bus for system communication
3. Build math utilities (Vector3, grid operations)
4. Add core utilities (logging, performance monitoring)
</paved_path>

<patterns>
- All core classes use abstract base classes for Unity portability
- Systems communicate only through events, never direct references
- Math operations use immutable value types
- Performance monitoring built into all core operations
</patterns>

<workflow>
Core implementation order: ECS → Events → Math → Utils
</workflow>

<example>
```python
# Core system interaction pattern
entity = EntityManager.create_entity()
entity.add_component(Transform())
EventBus.publish(EntityCreatedEvent(entity.id))
```
</example>