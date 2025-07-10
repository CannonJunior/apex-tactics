"""
Core Engine Systems

Fundamental engine infrastructure including ECS, events, math, and utilities.
"""

from .ecs.world import World
from .ecs.entity import Entity, EntityManager
from .ecs.component import BaseComponent, Transform, ComponentRegistry
from .ecs.system import BaseSystem, SystemManager
from .math.vector import Vector3, Vector2Int

# Optional events import to avoid circular dependencies
try:
    from .events import EventBus, GameEvent, EventType
    _events_available = True
except ImportError:
    EventBus = None
    GameEvent = None  
    EventType = None
    _events_available = False

__all__ = [
    'World',
    'Entity', 'EntityManager',
    'BaseComponent', 'Transform', 'ComponentRegistry',
    'BaseSystem', 'SystemManager',
    'Vector3', 'Vector2Int'
]

if _events_available:
    __all__.extend(['EventBus', 'GameEvent', 'EventType'])