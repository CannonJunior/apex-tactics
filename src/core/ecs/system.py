"""
System Base Classes for ECS Architecture

Implements the System part of Entity-Component-System pattern.
Systems contain all game logic and operate on entities with specific components.
"""

from abc import ABC, abstractmethod
from typing import List, Type, Set, Dict, Any
import time

from .entity import Entity
from .component import BaseComponent
from core.events.event_bus import EventBus

class BaseSystem(ABC):
    """
    Abstract base class for all game systems.
    
    Systems contain game logic and operate on entities that have
    required components. Each system processes entities during update.
    """
    
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self.enabled = True
        self.priority = 0  # Lower numbers = higher priority
        self.performance_stats = SystemPerformanceStats()
        
    @abstractmethod
    def get_required_components(self) -> Set[Type[BaseComponent]]:
        """
        Return set of component types this system requires.
        
        Only entities with ALL required components will be processed.
        
        Returns:
            Set of required component types
        """
        pass
    
    @abstractmethod
    def update(self, delta_time: float, entities: List[Entity]):
        """
        Update system logic for all matching entities.
        
        Args:
            delta_time: Time elapsed since last update in seconds
            entities: List of entities with required components
        """
        pass
    
    def on_entity_added(self, entity: Entity):
        """
        Called when entity with required components is added to world.
        
        Override to perform initialization when entities become relevant.
        
        Args:
            entity: Entity that was added
        """
        pass
    
    def on_entity_removed(self, entity: Entity):
        """
        Called when entity no longer has required components.
        
        Override to perform cleanup when entities become irrelevant.
        
        Args:
            entity: Entity that was removed
        """
        pass
    
    def initialize(self):
        """
        Initialize system before first update.
        
        Override to perform one-time system setup.
        """
        pass
    
    def shutdown(self):
        """
        Cleanup system resources.
        
        Override to perform system cleanup.
        """
        pass
    
    def get_optional_components(self) -> Set[Type[BaseComponent]]:
        """
        Return set of optional component types.
        
        Entities with required components are processed regardless
        of whether they have optional components.
        
        Returns:
            Set of optional component types
        """
        return set()
    
    def should_process_entity(self, entity: Entity) -> bool:
        """
        Check if entity should be processed by this system.
        
        Override for custom entity filtering logic.
        
        Args:
            entity: Entity to check
            
        Returns:
            True if entity should be processed
        """
        return entity.active and entity.has_components(*self.get_required_components())
    
    def _start_frame(self):
        """Internal: Start frame timing"""
        self.performance_stats.frame_start_time = time.perf_counter()
    
    def _end_frame(self, entity_count: int):
        """Internal: End frame timing"""
        end_time = time.perf_counter()
        frame_time = end_time - self.performance_stats.frame_start_time
        self.performance_stats.add_frame_time(frame_time, entity_count)

class SystemPerformanceStats:
    """Performance tracking for systems"""
    
    def __init__(self):
        self.frame_start_time = 0.0
        self.total_time = 0.0
        self.frame_count = 0
        self.total_entities_processed = 0
        self.max_frame_time = 0.0
        self.min_frame_time = float('inf')
        
    def add_frame_time(self, frame_time: float, entity_count: int):
        """Add frame timing data"""
        self.total_time += frame_time
        self.frame_count += 1
        self.total_entities_processed += entity_count
        self.max_frame_time = max(self.max_frame_time, frame_time)
        self.min_frame_time = min(self.min_frame_time, frame_time)
    
    @property
    def average_frame_time(self) -> float:
        """Get average frame time in seconds"""
        return self.total_time / self.frame_count if self.frame_count > 0 else 0.0
    
    @property
    def average_entities_per_frame(self) -> float:
        """Get average entities processed per frame"""
        return self.total_entities_processed / self.frame_count if self.frame_count > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting"""
        return {
            'total_time': self.total_time,
            'frame_count': self.frame_count,
            'total_entities_processed': self.total_entities_processed,
            'average_frame_time': self.average_frame_time,
            'average_entities_per_frame': self.average_entities_per_frame,
            'max_frame_time': self.max_frame_time,
            'min_frame_time': self.min_frame_time if self.min_frame_time != float('inf') else 0.0
        }

class SystemManager:
    """
    Manages and coordinates all game systems.
    
    Handles system registration, update ordering, and performance monitoring.
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._systems: List[BaseSystem] = []
        self._systems_by_name: Dict[str, BaseSystem] = {}
        self._initialized = False
    
    def add_system(self, system: BaseSystem):
        """
        Add system to manager.
        
        Args:
            system: System to add
            
        Raises:
            ValueError: If system with same name already exists
        """
        if system.name in self._systems_by_name:
            raise ValueError(f"System with name '{system.name}' already exists")
        
        self._systems.append(system)
        self._systems_by_name[system.name] = system
        
        # Sort systems by priority
        self._systems.sort(key=lambda s: s.priority)
        
        # Initialize if manager is already initialized
        if self._initialized:
            system.initialize()
    
    def remove_system(self, system_name: str) -> bool:
        """
        Remove system by name.
        
        Args:
            system_name: Name of system to remove
            
        Returns:
            True if system was found and removed
        """
        if system_name not in self._systems_by_name:
            return False
        
        system = self._systems_by_name[system_name]
        system.shutdown()
        
        self._systems.remove(system)
        del self._systems_by_name[system_name]
        
        return True
    
    def get_system(self, system_name: str) -> BaseSystem:
        """
        Get system by name.
        
        Args:
            system_name: Name of system to get
            
        Returns:
            System or None if not found
        """
        return self._systems_by_name.get(system_name)
    
    def initialize(self):
        """Initialize all systems"""
        for system in self._systems:
            system.initialize()
        self._initialized = True
    
    def update(self, delta_time: float, entities: List[Entity]):
        """
        Update all enabled systems.
        
        Args:
            delta_time: Time elapsed since last update
            entities: All entities in the world
        """
        for system in self._systems:
            if not system.enabled:
                continue
            
            # Filter entities for this system
            matching_entities = [
                entity for entity in entities 
                if system.should_process_entity(entity)
            ]
            
            # Update system with performance tracking
            system._start_frame()
            try:
                system.update(delta_time, matching_entities)
            except Exception as e:
                # Log error but continue with other systems
                print(f"Error in system {system.name}: {e}")
            finally:
                system._end_frame(len(matching_entities))
    
    def shutdown(self):
        """Shutdown all systems"""
        for system in reversed(self._systems):  # Shutdown in reverse order
            system.shutdown()
        self._initialized = False
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance report for all systems"""
        return {
            system.name: system.performance_stats.to_dict()
            for system in self._systems
        }
    
    def enable_system(self, system_name: str):
        """Enable system by name"""
        system = self.get_system(system_name)
        if system:
            system.enabled = True
    
    def disable_system(self, system_name: str):
        """Disable system by name"""
        system = self.get_system(system_name)
        if system:
            system.enabled = False
    
    def get_system_count(self) -> int:
        """Get total number of registered systems"""
        return len(self._systems)
    
    def get_enabled_system_count(self) -> int:
        """Get number of enabled systems"""
        return len([s for s in self._systems if s.enabled])