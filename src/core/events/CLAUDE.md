# Event System

<system_context>
Decoupled event-driven communication system enabling systems to interact without direct dependencies.
</system_context>

<critical_notes>
- Events are immutable once published
- Event handlers must not throw exceptions
- Event loop must process all events before frame end
- No synchronous event handling to prevent blocking
</critical_notes>

<file_map>
Event bus: @src/core/events/event_bus.py
Event type definitions: @src/core/events/event_types.py
Event listeners: @src/core/events/listeners.py
</file_map>

<paved_path>
1. Define base Event class
2. Implement EventBus with publish/subscribe
3. Create event listener registration system
4. Add event type definitions for game events
</paved_path>

<patterns>
```python
# Event publishing
EventBus.publish(EntityDestroyedEvent(entity_id))

# Event subscription
EventBus.subscribe(EntityDestroyedEvent, self.handle_entity_destroyed)
```
</patterns>

<fatal_implications>
Event handler exceptions can crash the entire event system.
</fatal_implications>