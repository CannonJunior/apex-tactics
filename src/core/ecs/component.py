"""
Base Component Classes for ECS Architecture

Implements the Component part of Entity-Component-System pattern.
Components are pure data containers with no behavior logic.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type
import time
import uuid

class BaseComponent(ABC):
    """
    Abstract base class for all game components.
    
    Components are pure data containers that can be attached to entities.
    All game logic is implemented in systems that operate on components.
    """
    
    def __init__(self):
        self.entity_id: Optional[str] = None
        self.created_at: float = time.time()
        self.component_id: str = str(uuid.uuid4())
        self._dirty: bool = True  # Mark for system updates
        
    @property
    def is_dirty(self) -> bool:
        """Check if component has been modified since last system update"""
        return self._dirty
    
    def mark_clean(self):
        """Mark component as processed by systems"""
        self._dirty = False
        
    def mark_dirty(self):
        """Mark component as needing system processing"""
        self._dirty = True
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize component to dictionary for saving/networking"""
        return {
            'component_type': self.__class__.__name__,
            'entity_id': self.entity_id,
            'created_at': self.created_at,
            'component_id': self.component_id
        }
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseComponent':
        """Deserialize component from dictionary"""
        pass
    
    def copy(self) -> 'BaseComponent':
        """Create a copy of this component"""
        data = self.to_dict()
        return self.__class__.from_dict(data)

class Transform(BaseComponent):
    """
    Transform component for entity position, rotation, and scale.
    
    Essential component for any entity that exists in 3D space.
    Uses Vector3 for position/scale and quaternion-like rotation.
    """
    
    def __init__(self, position=None, rotation=None, scale=None):
        super().__init__()
        from core.math.vector import Vector3
        
        self.position = position or Vector3(0.0, 0.0, 0.0)
        self.rotation = rotation or Vector3(0.0, 0.0, 0.0)  # Euler angles for simplicity
        self.scale = scale or Vector3(1.0, 1.0, 1.0)
    
    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            'position': self.position.to_dict(),
            'rotation': self.rotation.to_dict(),
            'scale': self.scale.to_dict()
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transform':
        from core.math.vector import Vector3
        
        transform = cls()
        transform.entity_id = data.get('entity_id')
        transform.created_at = data.get('created_at', time.time())
        transform.component_id = data.get('component_id', str(uuid.uuid4()))
        
        transform.position = Vector3.from_dict(data['position'])
        transform.rotation = Vector3.from_dict(data['rotation'])
        transform.scale = Vector3.from_dict(data['scale'])
        
        return transform

class ComponentRegistry:
    """
    Registry for all component types in the system.
    
    Provides component type lookup and validation for the ECS system.
    """
    
    _registered_components: Dict[str, Type[BaseComponent]] = {}
    
    @classmethod
    def register(cls, component_type: Type[BaseComponent]):
        """Register a component type with the registry"""
        type_name = component_type.__name__
        
        if type_name in cls._registered_components:
            # Allow re-registration (useful for testing)
            pass
        
        cls._registered_components[type_name] = component_type
    
    @classmethod
    def get_component_type(cls, type_name: str) -> Optional[Type[BaseComponent]]:
        """Get component type by name"""
        return cls._registered_components.get(type_name)
    
    @classmethod
    def is_registered(cls, component_type: Type[BaseComponent]) -> bool:
        """Check if component type is registered"""
        return component_type.__name__ in cls._registered_components
    
    @classmethod
    def get_all_types(cls) -> Dict[str, Type[BaseComponent]]:
        """Get all registered component types"""
        return cls._registered_components.copy()

# Register core components
ComponentRegistry.register(Transform)