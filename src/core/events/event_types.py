"""
Core Event Type Definitions

Defines standard events used throughout the ECS system.
Systems can publish and subscribe to these events for communication.
"""

from typing import Optional
from .event_bus import Event

# Entity Lifecycle Events

class EntityCreatedEvent(Event):
    """Published when a new entity is created"""
    
    def __init__(self, entity_id: str):
        super().__init__()
        self.entity_id = entity_id

class EntityDestroyedEvent(Event):
    """Published when an entity is destroyed"""
    
    def __init__(self, entity_id: str):
        super().__init__()
        self.entity_id = entity_id

class ComponentAddedEvent(Event):
    """Published when a component is added to an entity"""
    
    def __init__(self, entity_id: str, component_type: str):
        super().__init__()
        self.entity_id = entity_id
        self.component_type = component_type

class ComponentRemovedEvent(Event):
    """Published when a component is removed from an entity"""
    
    def __init__(self, entity_id: str, component_type: str):
        super().__init__()
        self.entity_id = entity_id
        self.component_type = component_type

# System Events

class SystemInitializedEvent(Event):
    """Published when a system is initialized"""
    
    def __init__(self, system_name: str):
        super().__init__()
        self.system_name = system_name

class SystemShutdownEvent(Event):
    """Published when a system is shutdown"""
    
    def __init__(self, system_name: str):
        super().__init__()
        self.system_name = system_name

# Game State Events

class GameStartedEvent(Event):
    """Published when the game starts"""
    
    def __init__(self):
        super().__init__()

class GamePausedEvent(Event):
    """Published when the game is paused"""
    
    def __init__(self):
        super().__init__()

class GameResumedEvent(Event):
    """Published when the game is resumed"""
    
    def __init__(self):
        super().__init__()

class GameEndedEvent(Event):
    """Published when the game ends"""
    
    def __init__(self, reason: str = ""):
        super().__init__()
        self.reason = reason

# Performance Events

class PerformanceWarningEvent(Event):
    """Published when performance thresholds are exceeded"""
    
    def __init__(self, system_name: str, frame_time: float, threshold: float):
        super().__init__()
        self.system_name = system_name
        self.frame_time = frame_time
        self.threshold = threshold

class MemoryWarningEvent(Event):
    """Published when memory usage is high"""
    
    def __init__(self, memory_usage: int, threshold: int):
        super().__init__()
        self.memory_usage = memory_usage
        self.threshold = threshold