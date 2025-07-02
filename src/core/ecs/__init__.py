"""
Entity Component System (ECS)

Core ECS implementation with Entity, Component, System, and World classes.
"""

from .entity import Entity, EntityManager
from .component import BaseComponent, Transform, ComponentRegistry
from .system import BaseSystem, SystemManager
from .world import World

# Aliases for backward compatibility
ECSManager = World
Component = BaseComponent
System = BaseSystem
EntityID = str

__all__ = [
    'Entity', 'EntityManager', 'ECSManager', 'EntityID',
    'BaseComponent', 'Component', 'Transform', 'ComponentRegistry', 
    'BaseSystem', 'System', 'SystemManager',
    'World'
]