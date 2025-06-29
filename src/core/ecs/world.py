"""
World Management for ECS Architecture

The World class coordinates entities, components, and systems.
It serves as the main container and coordinator for the ECS architecture.
"""

from typing import List, Type, Optional, Dict, Any
import time

from .entity import Entity, EntityManager
from .system import BaseSystem, SystemManager
from .component import BaseComponent
from core.events.event_bus import EventBus
from core.events.event_types import (
    EntityCreatedEvent, EntityDestroyedEvent,
    ComponentAddedEvent, ComponentRemovedEvent,
    GameStartedEvent, GamePausedEvent, GameResumedEvent, GameEndedEvent
)

class World:
    """
    Central world coordinator for the ECS system.
    
    Manages entities, systems, and coordinates their interactions.
    Provides high-level interface for game logic.
    """
    
    def __init__(self):
        self.entity_manager = EntityManager()
        self.event_bus = EventBus()
        self.system_manager = SystemManager(self.event_bus)
        
        self.running = False
        self.paused = False
        self.total_time = 0.0
        self.frame_count = 0
        
        # Performance tracking
        self.max_frame_time = 0.0
        self.performance_warning_threshold = 0.016  # 16ms (60 FPS)
        
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Setup internal event handlers"""
        # We can add internal event handling here if needed
        pass
    
    def add_system(self, system: BaseSystem):
        """
        Add system to the world.
        
        Args:
            system: System to add
        """
        self.system_manager.add_system(system)
    
    def remove_system(self, system_name: str) -> bool:
        """
        Remove system from the world.
        
        Args:
            system_name: Name of system to remove
            
        Returns:
            True if system was removed
        """
        return self.system_manager.remove_system(system_name)
    
    def get_system(self, system_name: str) -> Optional[BaseSystem]:
        """
        Get system by name.
        
        Args:
            system_name: Name of system to get
            
        Returns:
            System or None if not found
        """
        return self.system_manager.get_system(system_name)
    
    def create_entity(self, *components: BaseComponent) -> Entity:
        """
        Create new entity with optional components.
        
        Args:
            components: Components to add to entity
            
        Returns:
            Created entity
        """
        entity = self.entity_manager.create_entity(*components)
        
        # Publish entity creation event
        self.event_bus.publish(EntityCreatedEvent(entity.id))
        
        # Publish component addition events
        for component in components:
            self.event_bus.publish(ComponentAddedEvent(
                entity.id, component.__class__.__name__
            ))
        
        return entity
    
    def destroy_entity(self, entity_id: str) -> bool:
        """
        Destroy entity by ID.
        
        Args:
            entity_id: ID of entity to destroy
            
        Returns:
            True if entity was found and destroyed
        """
        entity = self.entity_manager.get_entity(entity_id)
        if not entity:
            return False
        
        # Publish component removal events
        for component_type in entity.get_component_types():
            self.event_bus.publish(ComponentRemovedEvent(
                entity_id, component_type.__name__
            ))
        
        # Destroy entity
        success = self.entity_manager.destroy_entity(entity_id)
        
        if success:
            # Publish entity destruction event
            self.event_bus.publish(EntityDestroyedEvent(entity_id))
        
        return success
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """
        Get entity by ID.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Entity or None if not found
        """
        return self.entity_manager.get_entity(entity_id)
    
    def get_entities_with_component(self, component_type: Type[BaseComponent]) -> List[Entity]:
        """
        Get entities that have specified component.
        
        Args:
            component_type: Component type to filter by
            
        Returns:
            List of entities with component
        """
        return self.entity_manager.get_entities_with_component(component_type)
    
    def get_entities_with_components(self, *component_types: Type[BaseComponent]) -> List[Entity]:
        """
        Get entities that have all specified components.
        
        Args:
            component_types: Component types that must all be present
            
        Returns:
            List of entities with all components
        """
        return self.entity_manager.get_entities_with_components(*component_types)
    
    def get_all_entities(self) -> List[Entity]:
        """Get all active entities in the world"""
        return self.entity_manager.get_all_entities()
    
    def initialize(self):
        """Initialize the world and all systems"""
        self.system_manager.initialize()
        self.event_bus.publish(GameStartedEvent())
        self.running = True
    
    def update(self, delta_time: float):
        """
        Update world for one frame.
        
        Args:
            delta_time: Time elapsed since last update in seconds
        """
        if not self.running or self.paused:
            return
        
        frame_start_time = time.perf_counter()
        
        # Clean up destroyed entities
        self.entity_manager.cleanup_destroyed_entities()
        
        # Get all entities for systems
        all_entities = self.get_all_entities()
        
        # Update all systems
        self.system_manager.update(delta_time, all_entities)
        
        # Process events
        self.event_bus.process_events()
        
        # Update timing statistics
        frame_end_time = time.perf_counter()
        frame_time = frame_end_time - frame_start_time
        
        self.total_time += delta_time
        self.frame_count += 1
        self.max_frame_time = max(self.max_frame_time, frame_time)
        
        # Check performance
        if frame_time > self.performance_warning_threshold:
            from core.events.event_types import PerformanceWarningEvent
            self.event_bus.publish(PerformanceWarningEvent(
                "World", frame_time, self.performance_warning_threshold
            ))
    
    def pause(self):
        """Pause world updates"""
        if self.running and not self.paused:
            self.paused = True
            self.event_bus.publish(GamePausedEvent())
    
    def resume(self):
        """Resume world updates"""
        if self.running and self.paused:
            self.paused = False
            self.event_bus.publish(GameResumedEvent())
    
    def shutdown(self):
        """Shutdown world and all systems"""
        if self.running:
            self.event_bus.publish(GameEndedEvent("shutdown"))
            self.system_manager.shutdown()
            self.running = False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get world statistics for debugging"""
        entity_stats = self.entity_manager.get_statistics()
        system_performance = self.system_manager.get_performance_report()
        event_stats = self.event_bus.get_stats()
        
        return {
            'world': {
                'running': self.running,
                'paused': self.paused,
                'total_time': self.total_time,
                'frame_count': self.frame_count,
                'average_fps': self.frame_count / self.total_time if self.total_time > 0 else 0,
                'max_frame_time': self.max_frame_time
            },
            'entities': entity_stats,
            'systems': {
                'system_count': self.system_manager.get_system_count(),
                'enabled_systems': self.system_manager.get_enabled_system_count(),
                'performance': system_performance
            },
            'events': event_stats
        }
    
    def enable_system(self, system_name: str):
        """Enable system by name"""
        self.system_manager.enable_system(system_name)
    
    def disable_system(self, system_name: str):
        """Disable system by name"""
        self.system_manager.disable_system(system_name)
    
    @property
    def entity_count(self) -> int:
        """Get total number of active entities"""
        return self.entity_manager.get_entity_count()
    
    @property
    def system_count(self) -> int:
        """Get total number of registered systems"""
        return self.system_manager.get_system_count()