"""
Entity Component System (ECS) Framework

Implements a flexible and performant ECS architecture for game entities,
components, and systems following Unity's design patterns for portability.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Set, Type, TypeVar, Generic
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from collections import defaultdict
import uuid

import structlog

logger = structlog.get_logger()

T = TypeVar('T', bound='Component')


class EntityID:
    """Unique entity identifier"""
    
    def __init__(self, value: Optional[str] = None):
        self.value = value or str(uuid.uuid4())
    
    def __str__(self) -> str:
        return self.value
    
    def __eq__(self, other) -> bool:
        return isinstance(other, EntityID) and self.value == other.value
    
    def __hash__(self) -> int:
        return hash(self.value)


class Component(ABC):
    """Base component class"""
    
    def __init__(self):
        self.entity_id: Optional[EntityID] = None
        self.enabled = True
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize component to dictionary"""
        pass
    
    @abstractmethod
    def from_dict(self, data: Dict[str, Any]):
        """Deserialize component from dictionary"""
        pass


class System(ABC):
    """Base system class"""
    
    def __init__(self, ecs_manager: 'ECSManager', event_bus=None):
        self.ecs = ecs_manager
        self.event_bus = event_bus
        self.enabled = True
        self.execution_order = 0
        self.required_components: Set[Type[Component]] = set()
        self._cached_entities: Dict[str, List[EntityID]] = {}
        self._cache_dirty = True
    
    @abstractmethod
    async def update(self, session_id: str, delta_time: float):
        """Update system logic"""
        pass
    
    def requires_components(self, *component_types: Type[Component]):
        """Specify required component types for this system"""
        self.required_components.update(component_types)
        self._cache_dirty = True
    
    def get_entities_with_components(self, session_id: str, 
                                   *component_types: Type[Component]) -> List[EntityID]:
        """Get entities that have all specified components"""
        if not component_types:
            component_types = tuple(self.required_components)
        
        cache_key = f"{session_id}_{hash(component_types)}"
        
        if self._cache_dirty or cache_key not in self._cached_entities:
            entities = []
            for entity_id in self.ecs.get_entities_in_session(session_id):
                if all(self.ecs.has_component(entity_id, comp_type) for comp_type in component_types):
                    entities.append(entity_id)
            
            self._cached_entities[cache_key] = entities
        
        return self._cached_entities[cache_key]
    
    def invalidate_cache(self):
        """Invalidate entity cache"""
        self._cache_dirty = True
        self._cached_entities.clear()
    
    async def on_entity_created(self, entity_id: EntityID):
        """Called when an entity is created"""
        self.invalidate_cache()
    
    async def on_entity_destroyed(self, entity_id: EntityID):
        """Called when an entity is destroyed"""
        self.invalidate_cache()
    
    async def on_component_added(self, entity_id: EntityID, component: Component):
        """Called when a component is added to an entity"""
        self.invalidate_cache()
    
    async def on_component_removed(self, entity_id: EntityID, component_type: Type[Component]):
        """Called when a component is removed from an entity"""
        self.invalidate_cache()


@dataclass
class Entity:
    """Entity container"""
    id: EntityID
    name: str = ""
    session_id: str = ""
    active: bool = True
    created_time: float = field(default_factory=time.time)
    tags: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        if isinstance(self.id, str):
            self.id = EntityID(self.id)


class ComponentManager:
    """Manages component storage and retrieval"""
    
    def __init__(self):
        # Components grouped by type for fast iteration
        self.components_by_type: Dict[Type[Component], Dict[EntityID, Component]] = defaultdict(dict)
        # All components for an entity
        self.entity_components: Dict[EntityID, Dict[Type[Component], Component]] = defaultdict(dict)
        # Component lookup for performance
        self.component_types: Set[Type[Component]] = set()
    
    def add_component(self, entity_id: EntityID, component: Component):
        """Add component to entity"""
        component_type = type(component)
        component.entity_id = entity_id
        
        self.components_by_type[component_type][entity_id] = component
        self.entity_components[entity_id][component_type] = component
        self.component_types.add(component_type)
    
    def remove_component(self, entity_id: EntityID, component_type: Type[Component]) -> bool:
        """Remove component from entity"""
        if component_type in self.components_by_type:
            if entity_id in self.components_by_type[component_type]:
                del self.components_by_type[component_type][entity_id]
                
                if entity_id in self.entity_components:
                    if component_type in self.entity_components[entity_id]:
                        del self.entity_components[entity_id][component_type]
                
                return True
        return False
    
    def get_component(self, entity_id: EntityID, component_type: Type[T]) -> Optional[T]:
        """Get component of specific type from entity"""
        if component_type in self.components_by_type:
            return self.components_by_type[component_type].get(entity_id)
        return None
    
    def has_component(self, entity_id: EntityID, component_type: Type[Component]) -> bool:
        """Check if entity has component of specific type"""
        return (component_type in self.components_by_type and 
                entity_id in self.components_by_type[component_type])
    
    def get_all_components(self, entity_id: EntityID) -> Dict[Type[Component], Component]:
        """Get all components for an entity"""
        return self.entity_components.get(entity_id, {})
    
    def get_components_of_type(self, component_type: Type[T]) -> Dict[EntityID, T]:
        """Get all components of a specific type"""
        return self.components_by_type.get(component_type, {})
    
    def remove_all_components(self, entity_id: EntityID):
        """Remove all components from entity"""
        if entity_id in self.entity_components:
            for component_type in list(self.entity_components[entity_id].keys()):
                self.remove_component(entity_id, component_type)
    
    def get_component_count(self) -> int:
        """Get total number of components"""
        return sum(len(components) for components in self.components_by_type.values())


class ECSManager:
    """Main ECS manager"""
    
    def __init__(self):
        self.entities: Dict[EntityID, Entity] = {}
        self.entities_by_session: Dict[str, Set[EntityID]] = defaultdict(set)
        self.component_manager = ComponentManager()
        self.systems: List[System] = []
        self.system_execution_order: List[System] = []
        
        # Performance tracking
        self.frame_count = 0
        self.total_update_time = 0.0
        self.system_performance: Dict[str, float] = {}
        
        logger.info("ECS Manager initialized")
    
    def create_entity(self, session_id: str, name: str = "", entity_id: Optional[str] = None) -> EntityID:
        """Create a new entity"""
        eid = EntityID(entity_id)
        entity = Entity(id=eid, name=name, session_id=session_id)
        
        self.entities[eid] = entity
        self.entities_by_session[session_id].add(eid)
        
        # Notify systems
        for system in self.systems:
            asyncio.create_task(system.on_entity_created(eid))
        
        logger.debug("Entity created", entity_id=str(eid), session_id=session_id, name=name)
        return eid
    
    def destroy_entity(self, entity_id: EntityID):
        """Destroy an entity and all its components"""
        if entity_id not in self.entities:
            return False
        
        entity = self.entities[entity_id]
        
        # Remove all components
        self.component_manager.remove_all_components(entity_id)
        
        # Remove from session tracking
        if entity.session_id in self.entities_by_session:
            self.entities_by_session[entity.session_id].discard(entity_id)
        
        # Remove entity
        del self.entities[entity_id]
        
        # Notify systems
        for system in self.systems:
            asyncio.create_task(system.on_entity_destroyed(entity_id))
        
        logger.debug("Entity destroyed", entity_id=str(entity_id))
        return True
    
    def get_entity(self, entity_id: EntityID) -> Optional[Entity]:
        """Get entity by ID"""
        return self.entities.get(entity_id)
    
    def get_entities_in_session(self, session_id: str) -> Set[EntityID]:
        """Get all entities in a session"""
        return self.entities_by_session.get(session_id, set())
    
    def add_component(self, entity_id: EntityID, component: Component):
        """Add component to entity"""
        if entity_id not in self.entities:
            raise ValueError(f"Entity {entity_id} does not exist")
        
        self.component_manager.add_component(entity_id, component)
        
        # Notify systems
        for system in self.systems:
            asyncio.create_task(system.on_component_added(entity_id, component))
        
        logger.debug("Component added", 
                    entity_id=str(entity_id), 
                    component_type=type(component).__name__)
    
    def remove_component(self, entity_id: EntityID, component_type: Type[Component]) -> bool:
        """Remove component from entity"""
        success = self.component_manager.remove_component(entity_id, component_type)
        
        if success:
            # Notify systems
            for system in self.systems:
                asyncio.create_task(system.on_component_removed(entity_id, component_type))
            
            logger.debug("Component removed", 
                        entity_id=str(entity_id), 
                        component_type=component_type.__name__)
        
        return success
    
    def get_component(self, entity_id: EntityID, component_type: Type[T]) -> Optional[T]:
        """Get component from entity"""
        return self.component_manager.get_component(entity_id, component_type)
    
    def has_component(self, entity_id: EntityID, component_type: Type[Component]) -> bool:
        """Check if entity has component"""
        return self.component_manager.has_component(entity_id, component_type)
    
    def get_all_components(self, entity_id: EntityID) -> Dict[Type[Component], Component]:
        """Get all components for entity"""
        return self.component_manager.get_all_components(entity_id)
    
    def get_components_of_type(self, component_type: Type[T]) -> Dict[EntityID, T]:
        """Get all components of specific type"""
        return self.component_manager.get_components_of_type(component_type)
    
    def register_system(self, system: System):
        """Register a system"""
        self.systems.append(system)
        self._sort_systems()
        
        logger.info("System registered", 
                   system_type=type(system).__name__, 
                   execution_order=system.execution_order)
    
    def unregister_system(self, system: System):
        """Unregister a system"""
        if system in self.systems:
            self.systems.remove(system)
            self._sort_systems()
            
            logger.info("System unregistered", system_type=type(system).__name__)
    
    def _sort_systems(self):
        """Sort systems by execution order"""
        self.system_execution_order = sorted(self.systems, key=lambda s: s.execution_order)
    
    async def update(self, session_id: str, delta_time: Optional[float] = None):
        """Update all systems"""
        if delta_time is None:
            delta_time = 1.0 / 60.0  # Default to 60 FPS
        
        update_start = time.time()
        
        # Update systems in order
        for system in self.system_execution_order:
            if not system.enabled:
                continue
            
            system_start = time.time()
            
            try:
                await system.update(session_id, delta_time)
            except Exception as e:
                logger.error("System update failed", 
                           system=type(system).__name__, 
                           error=str(e))
            
            system_time = time.time() - system_start
            system_name = type(system).__name__
            self.system_performance[system_name] = system_time
        
        total_time = time.time() - update_start
        self.total_update_time += total_time
        self.frame_count += 1
    
    def find_entities_with_tag(self, session_id: str, tag: str) -> List[EntityID]:
        """Find entities with specific tag"""
        entities = []
        for entity_id in self.get_entities_in_session(session_id):
            entity = self.get_entity(entity_id)
            if entity and tag in entity.tags:
                entities.append(entity_id)
        return entities
    
    def find_entity_by_name(self, session_id: str, name: str) -> Optional[EntityID]:
        """Find entity by name"""
        for entity_id in self.get_entities_in_session(session_id):
            entity = self.get_entity(entity_id)
            if entity and entity.name == name:
                return entity_id
        return None
    
    def cleanup_session(self, session_id: str):
        """Clean up all entities in a session"""
        entity_ids = list(self.get_entities_in_session(session_id))
        
        for entity_id in entity_ids:
            self.destroy_entity(entity_id)
        
        # Clean up session tracking
        if session_id in self.entities_by_session:
            del self.entities_by_session[session_id]
        
        logger.info("Session cleaned up", 
                   session_id=session_id, 
                   entities_destroyed=len(entity_ids))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get ECS performance statistics"""
        avg_frame_time = (self.total_update_time / self.frame_count 
                         if self.frame_count > 0 else 0)
        
        return {
            "total_entities": len(self.entities),
            "total_components": self.component_manager.get_component_count(),
            "total_systems": len(self.systems),
            "frame_count": self.frame_count,
            "average_frame_time": avg_frame_time,
            "total_update_time": self.total_update_time,
            "system_performance": self.system_performance.copy(),
            "sessions_active": len(self.entities_by_session),
            "component_types": len(self.component_manager.component_types)
        }
    
    def serialize_entity(self, entity_id: EntityID) -> Dict[str, Any]:
        """Serialize entity and its components"""
        entity = self.get_entity(entity_id)
        if not entity:
            return {}
        
        components_data = {}
        for component_type, component in self.get_all_components(entity_id).items():
            components_data[component_type.__name__] = component.to_dict()
        
        return {
            "id": str(entity.id),
            "name": entity.name,
            "session_id": entity.session_id,
            "active": entity.active,
            "created_time": entity.created_time,
            "tags": list(entity.tags),
            "components": components_data
        }
    
    def deserialize_entity(self, data: Dict[str, Any], component_types: Dict[str, Type[Component]]) -> EntityID:
        """Deserialize entity from data"""
        entity_id = self.create_entity(
            session_id=data["session_id"],
            name=data.get("name", ""),
            entity_id=data["id"]
        )
        
        entity = self.get_entity(entity_id)
        if entity:
            entity.active = data.get("active", True)
            entity.created_time = data.get("created_time", time.time())
            entity.tags = set(data.get("tags", []))
        
        # Deserialize components
        components_data = data.get("components", {})
        for component_name, component_data in components_data.items():
            if component_name in component_types:
                component_type = component_types[component_name]
                component = component_type()
                component.from_dict(component_data)
                self.add_component(entity_id, component)
        
        return entity_id
    
    async def shutdown(self):
        """Shutdown ECS manager"""
        logger.info("Shutting down ECS manager")
        
        # Clean up all sessions
        for session_id in list(self.entities_by_session.keys()):
            self.cleanup_session(session_id)
        
        # Clear systems
        self.systems.clear()
        self.system_execution_order.clear()
        
        logger.info("ECS manager shutdown complete")