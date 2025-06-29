"""
Core Engine Systems

Fundamental engine infrastructure including ECS, events, math, and utilities.
"""

from .ecs.world import World
from .ecs.entity import Entity, EntityManager
from .ecs.component import BaseComponent, Transform, ComponentRegistry
from .ecs.system import BaseSystem, SystemManager
from .events.event_bus import EventBus, Event
from .math.vector import Vector3, Vector2Int

__all__ = [
    'World',
    'Entity', 'EntityManager',
    'BaseComponent', 'Transform', 'ComponentRegistry',
    'BaseSystem', 'SystemManager',
    'EventBus', 'Event',
    'Vector3', 'Vector2Int'
]