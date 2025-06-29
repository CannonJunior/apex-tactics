# Entity Component System (ECS)

<system_context>
Core ECS architecture providing Entity, Component, System abstractions for modular game object management.
</system_context>

<critical_notes>
- Entity IDs must be globally unique across entire game world
- Components are pure data - no behavior logic
- Systems contain all behavior logic and operate on components
- Component registration must happen before entity creation
</critical_notes>

<file_map>
Base entity class: @src/core/ecs/entity.py
Component base classes: @src/core/ecs/component.py
System base classes: @src/core/ecs/system.py
World management: @src/core/ecs/world.py
</file_map>

<paved_path>
1. Create BaseComponent abstract class
2. Implement Entity with component management
3. Create BaseSystem with update lifecycle
4. Build World as entity container and system manager
</paved_path>

<patterns>
```python
# Entity creation pattern
entity = EntityManager.create_entity()
entity.add_component(ComponentType())

# System update pattern
class MySystem(BaseSystem):
    def update(self, delta_time, entities):
        for entity in entities.with_component(MyComponent):
            # Process entity
```
</patterns>

<workflow>
1. Define component interfaces
2. Implement entity management
3. Create system base class
4. Build world as coordinator
</workflow>

<fatal_implications>
Circular component dependencies will cause infinite loops and system crashes.
</fatal_implications>