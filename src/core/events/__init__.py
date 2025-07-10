"""
Core Events Package

Event handling system for decoupled communication between game systems.
"""

# Import the main EventBus and types from events.py 
from ..events import EventBus, GameEvent, EventType

# Also import from local event_bus for compatibility
from .event_bus import Event, EventSubscription, get_event_bus

__all__ = ['Event', 'EventBus', 'EventSubscription', 'get_event_bus', 'GameEvent', 'EventType']