"""
Event System

Event-driven communication system for decoupled system interactions.
"""

from .event_bus import Event, EventBus
from .event_types import *

__all__ = [
    'Event', 'EventBus',
    'EntityCreatedEvent', 'EntityDestroyedEvent',
    'ComponentAddedEvent', 'ComponentRemovedEvent',
    'SystemInitializedEvent', 'SystemShutdownEvent',
    'GameStartedEvent', 'GamePausedEvent', 'GameResumedEvent', 'GameEndedEvent',
    'PerformanceWarningEvent', 'MemoryWarningEvent'
]