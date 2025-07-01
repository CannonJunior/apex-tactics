"""
Entity Component System (ECS)

Core ECS implementation with Entity, Component, System, and World classes.
"""

from .entity import Entity, EntityManager
from .component import BaseComponent, Transform, ComponentRegistry
from .system import BaseSystem, SystemManager
from .world import World

__all__ = [
    'Entity', 'EntityManager',
    'BaseComponent', 'Transform', 'ComponentRegistry', 
    'BaseSystem', 'SystemManager',
    'World'
]