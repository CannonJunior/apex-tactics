"""
Core Events Package

Event handling system for decoupled communication between game systems.
"""

from .event_bus import Event, EventBus, EventSubscription, get_event_bus

# Aliases for compatibility
GameEvent = Event
EventType = str  # Simple string type for event types

__all__ = ['Event', 'EventBus', 'EventSubscription', 'get_event_bus', 'GameEvent', 'EventType']