"""
Base Manager Class

Foundation for all game managers with event handling and lifecycle management.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseManager(ABC):
    """
    Base class for all game managers.
    
    Provides common functionality for event handling, initialization,
    and integration with the main game controller.
    """
    
    def __init__(self, game_controller):
        """
        Initialize base manager.
        
        Args:
            game_controller: Reference to main TacticalRPG controller
        """
        self.game_controller = game_controller
        self.is_initialized = False
        self.is_active = True
        
        # Will be set when event bus is available
        self.event_bus = getattr(game_controller, 'event_bus', None)
        
        # Manager-specific state
        self._state = {}
        
    def initialize(self):
        """Initialize the manager. Override in subclasses."""
        if self.is_initialized:
            return
            
        self._perform_initialization()
        self.is_initialized = True
        print(f"✅ {self.__class__.__name__} initialized")
    
    def _perform_initialization(self):
        """Override this method for manager-specific initialization."""
        pass
    
    def shutdown(self):
        """Cleanup when manager is shut down."""
        self.is_active = False
        self._perform_cleanup()
        print(f"🔄 {self.__class__.__name__} shut down")
    
    def _perform_cleanup(self):
        """Override this method for manager-specific cleanup."""
        pass
    
    def handle_event(self, event_type: str, data: Any = None):
        """
        Handle events from the event bus.
        
        Args:
            event_type: Type of event to handle
            data: Event data payload
        """
        if not self.is_active:
            return
            
        # Dispatch to specific handler methods
        handler_method = f"on_{event_type.lower()}"
        if hasattr(self, handler_method):
            handler = getattr(self, handler_method)
            handler(data)
    
    def emit_event(self, event_type: str, data: Any = None):
        """
        Emit an event through the event bus.
        
        Args:
            event_type: Type of event to emit
            data: Event data payload
        """
        if self.event_bus:
            self.event_bus.emit(event_type, data)
        else:
            # Fallback to direct controller notification during migration
            self._fallback_notify(event_type, data)
    
    def _fallback_notify(self, event_type: str, data: Any = None):
        """Fallback notification during migration when event bus not available."""
        # Can be overridden by managers that need immediate notification
        pass
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get manager state value."""
        return self._state.get(key, default)
    
    def set_state(self, key: str, value: Any):
        """Set manager state value."""
        self._state[key] = value
    
    def reset_state(self):
        """Reset manager state to initial values."""
        self._state.clear()
    
    @property
    def name(self) -> str:
        """Get manager name for logging and debugging."""
        return self.__class__.__name__


class ManagerRegistry:
    """Registry for managing all game managers."""
    
    def __init__(self):
        self.managers: Dict[str, BaseManager] = {}
        self.initialization_order = []
    
    def register(self, name: str, manager: BaseManager, initialize_immediately: bool = True):
        """Register a manager."""
        self.managers[name] = manager
        if initialize_immediately:
            manager.initialize()
            self.initialization_order.append(name)
        print(f"📝 Registered manager: {name}")
    
    def get(self, name: str) -> Optional[BaseManager]:
        """Get a manager by name."""
        return self.managers.get(name)
    
    def initialize_all(self):
        """Initialize all registered managers."""
        for name, manager in self.managers.items():
            if not manager.is_initialized:
                manager.initialize()
                if name not in self.initialization_order:
                    self.initialization_order.append(name)
    
    def shutdown_all(self):
        """Shutdown all managers in reverse initialization order."""
        for name in reversed(self.initialization_order):
            manager = self.managers.get(name)
            if manager and manager.is_active:
                manager.shutdown()
    
    def list_managers(self):
        """List all registered managers and their status."""
        for name, manager in self.managers.items():
            status = "✅ Active" if manager.is_active else "❌ Inactive"
            init_status = "✅ Initialized" if manager.is_initialized else "⏳ Pending"
            print(f"  {name}: {status}, {init_status}")