"""
Entity Management for ECS Architecture

Implements Entity class and EntityManager for the ECS system.
Entities are containers for components with unique identifiers.
"""

import uuid
import time
from typing import Dict, List, Optional, Type, TypeVar, Set
from .component import BaseComponent, ComponentRegistry

T = TypeVar('T', bound=BaseComponent)

class Entity:
    """
    Entity represents a game object as a collection of components.
    
    Entities have no behavior - they are pure containers for components.
    All game logic is implemented in systems that operate on components.
    """
    
    def __init__(self, entity_id: Optional[str] = None):
        self.id: str = entity_id or str(uuid.uuid4())
        self.created_at: float = time.time()
        self.active: bool = True
        self._components: Dict[Type[BaseComponent], BaseComponent] = {}
        self._component_types: Set[Type[BaseComponent]] = set()
    
    def add_component(self, component: BaseComponent) -> 'Entity':
        """
        Add a component to this entity.
        
        Args:
            component: Component instance to add
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If component type already exists on entity
        """
        component_type = type(component)
        
        if component_type in self._components:
            raise ValueError(f"Entity {self.id} already has component {component_type.__name__}")
        
        # Set bidirectional reference
        component.entity_id = self.id
        
        # Store component
        self._components[component_type] = component
        self._component_types.add(component_type)
        
        return self
    
    def remove_component(self, component_type: Type[T]) -> Optional[T]:
        """
        Remove a component from this entity.
        
        Args:
            component_type: Type of component to remove
            
        Returns:
            Removed component or None if not found
        """
        if component_type not in self._components:
            return None
        
        component = self._components.pop(component_type)
        self._component_types.discard(component_type)
        
        # Clear entity reference
        component.entity_id = None
        
        return component
    
    def get_component(self, component_type: Type[T]) -> Optional[T]:
        """
        Get component of specified type.
        
        Args:
            component_type: Type of component to retrieve
            
        Returns:
            Component instance or None if not found
        """
        return self._components.get(component_type)
    
    def has_component(self, component_type: Type[BaseComponent]) -> bool:
        """
        Check if entity has component of specified type.
        
        Args:
            component_type: Type of component to check
            
        Returns:
            True if component exists
        """
        return component_type in self._component_types
    
    def has_components(self, *component_types: Type[BaseComponent]) -> bool:
        """
        Check if entity has all specified component types.
        
        Args:
            component_types: Component types to check
            
        Returns:
            True if all components exist
        """
        return all(comp_type in self._component_types for comp_type in component_types)
    
    def get_all_components(self) -> List[BaseComponent]:
        """Get list of all components on this entity"""
        return list(self._components.values())
    
    def get_component_types(self) -> Set[Type[BaseComponent]]:
        """Get set of all component types on this entity"""
        return self._component_types.copy()
    
    def destroy(self):
        """
        Mark entity for destruction and cleanup components.
        
        This doesn't immediately remove the entity from the world,
        but marks it for cleanup during the next update cycle.
        """
        self.active = False
        
        # Clear component references
        for component in self._components.values():
            component.entity_id = None
        
        self._components.clear()
        self._component_types.clear()
    
    def to_dict(self) -> Dict[str, any]:
        """Serialize entity to dictionary"""
        return {
            'id': self.id,
            'created_at': self.created_at,
            'active': self.active,
            'components': {
                comp_type.__name__: component.to_dict() 
                for comp_type, component in self._components.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'Entity':
        """Deserialize entity from dictionary"""
        entity = cls(data['id'])
        entity.created_at = data.get('created_at', time.time())
        entity.active = data.get('active', True)
        
        # Reconstruct components
        components_data = data.get('components', {})
        for comp_type_name, comp_data in components_data.items():
            comp_type = ComponentRegistry.get_component_type(comp_type_name)
            if comp_type:
                component = comp_type.from_dict(comp_data)
                entity.add_component(component)
        
        return entity
    
    def __str__(self) -> str:
        component_names = [comp_type.__name__ for comp_type in self._component_types]
        return f"Entity({self.id[:8]}..., components={component_names})"
    
    def __repr__(self) -> str:
        return self.__str__()

class EntityManager:
    """
    Manages entity creation, destruction, and queries.
    
    Provides centralized entity management for the ECS system.
    Supports efficient component-based queries for systems.
    """
    
    def __init__(self):
        self._entities: Dict[str, Entity] = {}
        self._entities_by_components: Dict[Type[BaseComponent], Set[str]] = {}
        self._destroyed_entities: Set[str] = set()
        
        # Performance optimization: Cache filtered entity query results
        self._entity_query_cache: Dict[tuple, List[Entity]] = {}
        self._cache_invalidation_counter = 0
        self._max_cache_size = 50  # Limit cache size to prevent memory bloat
    
    def create_entity(self, *components: BaseComponent) -> Entity:
        """
        Create new entity with optional initial components.
        
        Args:
            components: Components to add to new entity
            
        Returns:
            Created entity
        """
        entity = Entity()
        
        # Add initial components
        for component in components:
            entity.add_component(component)
        
        # Register entity
        self._register_entity(entity)
        
        return entity
    
    def destroy_entity(self, entity_id: str) -> bool:
        """
        Mark entity for destruction.
        
        Args:
            entity_id: ID of entity to destroy
            
        Returns:
            True if entity was found and marked for destruction
        """
        if entity_id not in self._entities:
            return False
        
        entity = self._entities[entity_id]
        entity.destroy()
        self._destroyed_entities.add(entity_id)
        
        return True
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """
        Get entity by ID.
        
        Args:
            entity_id: Entity ID to lookup
            
        Returns:
            Entity or None if not found
        """
        return self._entities.get(entity_id)
    
    def get_entities_with_component(self, component_type: Type[BaseComponent]) -> List[Entity]:
        """
        Get all entities that have specified component type.
        
        Args:
            component_type: Component type to filter by
            
        Returns:
            List of entities with component
        """
        entity_ids = self._entities_by_components.get(component_type, set())
        return [self._entities[eid] for eid in entity_ids if eid in self._entities]
    
    def get_entities_with_components(self, *component_types: Type[BaseComponent]) -> List[Entity]:
        """
        Get all entities that have ALL specified component types.
        Uses caching for improved performance on repeated queries.
        
        Args:
            component_types: Component types that must all be present
            
        Returns:
            List of entities with all components
        """
        if not component_types:
            return list(self._entities.values())
        
        # Check cache first
        cache_key = self._get_cache_key(*component_types)
        if cache_key in self._entity_query_cache:
            # Return cached result, but filter out destroyed entities
            cached_entities = self._entity_query_cache[cache_key]
            return [entity for entity in cached_entities if entity.id in self._entities and entity.active]
        
        # Cache miss - compute result
        # Start with entities that have the first component type
        result_ids = self._entities_by_components.get(component_types[0], set()).copy()
        
        # Intersect with entities that have each additional component type
        for component_type in component_types[1:]:
            component_entity_ids = self._entities_by_components.get(component_type, set())
            result_ids &= component_entity_ids
        
        # Build result list
        result_entities = [self._entities[eid] for eid in result_ids if eid in self._entities and self._entities[eid].active]
        
        # Cache the result
        self._manage_cache_size()
        self._entity_query_cache[cache_key] = result_entities
        
        return result_entities
    
    def _invalidate_query_cache(self):
        """Invalidate entity query cache when components change"""
        self._entity_query_cache.clear()
        self._cache_invalidation_counter += 1
    
    def _get_cache_key(self, *component_types: Type[BaseComponent]) -> tuple:
        """Generate cache key for component query"""
        return tuple(sorted(comp.__name__ for comp in component_types))
    
    def _manage_cache_size(self):
        """Ensure cache doesn't grow too large"""
        if len(self._entity_query_cache) > self._max_cache_size:
            # Remove oldest half of cache entries (simple eviction)
            keys_to_remove = list(self._entity_query_cache.keys())[:self._max_cache_size // 2]
            for key in keys_to_remove:
                del self._entity_query_cache[key]
    
    def get_all_entities(self) -> List[Entity]:
        """Get all active entities"""
        return [entity for entity in self._entities.values() if entity.active]
    
    def cleanup_destroyed_entities(self):
        """Remove destroyed entities from manager"""
        for entity_id in self._destroyed_entities:
            if entity_id in self._entities:
                entity = self._entities[entity_id]
                
                # Remove from component indices
                for component_type in entity.get_component_types():
                    if component_type in self._entities_by_components:
                        self._entities_by_components[component_type].discard(entity_id)
                
                # Remove from entities dict
                del self._entities[entity_id]
        
        # Invalidate query cache when entities are destroyed
        if self._destroyed_entities:
            self._invalidate_query_cache()
            
        self._destroyed_entities.clear()
    
    def _register_entity(self, entity: Entity):
        """Register entity and update component indices"""
        self._entities[entity.id] = entity
        
        # Update component indices
        for component_type in entity.get_component_types():
            if component_type not in self._entities_by_components:
                self._entities_by_components[component_type] = set()
            self._entities_by_components[component_type].add(entity.id)
        
        # Invalidate query cache when new entities are registered
        if entity.get_component_types():
            self._invalidate_query_cache()
    
    def get_entity_count(self) -> int:
        """Get total number of active entities"""
        return len([e for e in self._entities.values() if e.active])
    
    def get_statistics(self) -> Dict[str, any]:
        """Get manager statistics for debugging"""
        component_counts = {
            comp_type.__name__: len(entity_ids)
            for comp_type, entity_ids in self._entities_by_components.items()
        }
        
        return {
            'total_entities': len(self._entities),
            'active_entities': self.get_entity_count(),
            'destroyed_pending': len(self._destroyed_entities),
            'component_counts': component_counts
        }