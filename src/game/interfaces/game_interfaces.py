"""
Game Module Interfaces

Defines clear contracts between modular components extracted from
the monolithic TacticalRPG controller. These interfaces ensure
proper separation of concerns and maintainable module interactions.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple, Callable
from enum import Enum

from core.models.unit import Unit


class InputEvent:
    """Represents an input event from keyboard or mouse."""
    
    def __init__(self, event_type: str, key: str = None, position: Tuple[int, int] = None, context: Dict[str, Any] = None):
        self.event_type = event_type  # 'key', 'mouse_click', 'mouse_move'
        self.key = key
        self.position = position
        self.context = context or {}
        self.handled = False


class GameEvent:
    """Represents a game state event."""
    
    def __init__(self, event_type: str, data: Dict[str, Any] = None, source: str = None):
        self.event_type = event_type
        self.data = data or {}
        self.source = source
        self.timestamp = None  # Will be set by event system


class ModalType(Enum):
    """Types of modal dialogs."""
    ACTION = "action"
    MOVEMENT = "movement"
    ATTACK = "attack"
    MAGIC = "magic"
    TALENT = "talent"


class HighlightType(Enum):
    """Types of tile highlighting."""
    MOVEMENT = "movement"
    ATTACK = "attack"
    MAGIC = "magic"
    TALENT = "talent"
    PATH = "path"
    SELECTION = "selection"
    EFFECT_AREA = "effect_area"


# Core Module Interfaces

class IGameStateManager(ABC):
    """Interface for game state management."""
    
    @abstractmethod
    def get_active_unit(self) -> Optional[Unit]:
        """Get the currently active unit."""
        pass
    
    @abstractmethod
    def set_active_unit(self, unit: Optional[Unit], context: Dict[str, Any] = None):
        """Set the active unit."""
        pass
    
    @abstractmethod
    def get_current_mode(self) -> str:
        """Get the current interaction mode."""
        pass
    
    @abstractmethod
    def set_mode(self, mode: str, context: Dict[str, Any] = None):
        """Set the interaction mode."""
        pass
    
    @abstractmethod
    def end_current_turn(self) -> bool:
        """End current turn and advance."""
        pass
    
    @abstractmethod
    def is_battle_active(self) -> bool:
        """Check if battle is active."""
        pass


class IInputManager(ABC):
    """Interface for input handling."""
    
    @abstractmethod
    def handle_input(self, event: InputEvent) -> bool:
        """Handle an input event. Returns True if handled."""
        pass
    
    @abstractmethod
    def register_modal(self, modal_id: str, priority: int):
        """Register a modal for input priority."""
        pass
    
    @abstractmethod
    def unregister_modal(self, modal_id: str):
        """Unregister a modal."""
        pass
    
    @abstractmethod
    def set_input_mode(self, mode: str):
        """Set the input processing mode."""
        pass


class IModalManager(ABC):
    """Interface for modal management."""
    
    @abstractmethod
    def show_modal(self, modal_type: ModalType, context: Dict[str, Any]) -> str:
        """Show a modal dialog. Returns modal ID."""
        pass
    
    @abstractmethod
    def hide_modal(self, modal_id: str):
        """Hide a modal dialog."""
        pass
    
    @abstractmethod
    def is_modal_active(self) -> bool:
        """Check if any modal is active."""
        pass
    
    @abstractmethod
    def get_active_modal(self) -> Optional[str]:
        """Get the currently active modal ID."""
        pass


class IHighlightManager(ABC):
    """Interface for visual highlighting."""
    
    @abstractmethod
    def highlight_tiles(self, tiles: List[Tuple[int, int]], highlight_type: HighlightType):
        """Highlight specified tiles."""
        pass
    
    @abstractmethod
    def clear_highlights(self, highlight_type: Optional[HighlightType] = None):
        """Clear highlights of specified type, or all if None."""
        pass
    
    @abstractmethod
    def highlight_path(self, path: List[Tuple[int, int]]):
        """Highlight a movement path."""
        pass
    
    @abstractmethod
    def highlight_unit(self, unit: Unit, highlight_type: HighlightType):
        """Highlight a unit."""
        pass


class IUIManager(ABC):
    """Interface for UI element management."""
    
    @abstractmethod
    def update_unit_bars(self, unit: Optional[Unit]):
        """Update health/resource bars for unit."""
        pass
    
    @abstractmethod
    def update_hotkey_slots(self, abilities: List[Dict[str, Any]]):
        """Update hotkey slot displays."""
        pass
    
    @abstractmethod
    def show_targeted_bars(self, units: List[Unit]):
        """Show bars for targeted units."""
        pass
    
    @abstractmethod
    def hide_all_bars(self):
        """Hide all UI bars."""
        pass
    
    @abstractmethod
    def sync_ui_state(self):
        """Synchronize UI with current game state."""
        pass


class IActionManager(ABC):
    """Interface for action execution."""
    
    @abstractmethod
    def execute_action(self, action_type: str, source: Unit, target: Optional[Unit] = None, context: Dict[str, Any] = None) -> bool:
        """Execute an action. Returns True if successful."""
        pass
    
    @abstractmethod
    def validate_action(self, action_type: str, source: Unit, target: Optional[Unit] = None, context: Dict[str, Any] = None) -> bool:
        """Validate if action can be executed."""
        pass
    
    @abstractmethod
    def get_action_targets(self, action_type: str, source: Unit, position: Tuple[int, int]) -> List[Unit]:
        """Get potential targets for an action."""
        pass
    
    @abstractmethod
    def get_action_range(self, action_type: str, source: Unit) -> int:
        """Get the range of an action."""
        pass


class IMovementManager(ABC):
    """Interface for movement and pathfinding."""
    
    @abstractmethod
    def calculate_path(self, start: Tuple[int, int], end: Tuple[int, int], unit: Unit) -> List[Tuple[int, int]]:
        """Calculate movement path."""
        pass
    
    @abstractmethod
    def validate_movement(self, unit: Unit, path: List[Tuple[int, int]]) -> bool:
        """Validate if movement is legal."""
        pass
    
    @abstractmethod
    def execute_movement(self, unit: Unit, path: List[Tuple[int, int]]) -> bool:
        """Execute unit movement."""
        pass
    
    @abstractmethod
    def get_movement_range(self, unit: Unit) -> List[Tuple[int, int]]:
        """Get all valid movement positions."""
        pass


# Event System Interface

class IEventBus(ABC):
    """Interface for event communication between modules."""
    
    @abstractmethod
    def publish(self, event: GameEvent):
        """Publish an event."""
        pass
    
    @abstractmethod
    def subscribe(self, event_type: str, callback: Callable[[GameEvent], None]):
        """Subscribe to event type."""
        pass
    
    @abstractmethod
    def unsubscribe(self, event_type: str, callback: Callable[[GameEvent], None]):
        """Unsubscribe from event type."""
        pass


# Module Configuration

class ModuleConfig:
    """Configuration for module initialization."""
    
    def __init__(self):
        self.grid_width = 10
        self.grid_height = 8
        self.enable_visual_highlights = True
        self.enable_ui_animations = True
        self.enable_sound_effects = False
        self.debug_mode = False


# Dependency Container

class ModuleDependencies:
    """Container for module dependencies."""
    
    def __init__(self):
        self.game_state: Optional[IGameStateManager] = None
        self.input_manager: Optional[IInputManager] = None
        self.modal_manager: Optional[IModalManager] = None
        self.highlight_manager: Optional[IHighlightManager] = None
        self.ui_manager: Optional[IUIManager] = None
        self.action_manager: Optional[IActionManager] = None
        self.movement_manager: Optional[IMovementManager] = None
        self.event_bus: Optional[IEventBus] = None
        self.config: ModuleConfig = ModuleConfig()
    
    def validate(self) -> bool:
        """Validate that all required dependencies are set."""
        required = [
            self.game_state,
            self.input_manager,
            self.modal_manager,
            self.highlight_manager,
            self.ui_manager,
            self.action_manager,
            self.movement_manager,
            self.event_bus
        ]
        
        missing = [dep for dep in required if dep is None]
        if missing:
            print(f"❌ Missing dependencies: {len(missing)} modules")
            return False
        
        print("✅ All module dependencies satisfied")
        return True


# Common Event Types

class EventTypes:
    """Standard event type constants."""
    
    # Game State Events
    ACTIVE_UNIT_CHANGED = "active_unit_changed"
    MODE_CHANGED = "mode_changed"
    TURN_ENDED = "turn_ended"
    BATTLE_STATE_CHANGED = "battle_state_changed"
    
    # Input Events
    TILE_CLICKED = "tile_clicked"
    HOTKEY_PRESSED = "hotkey_pressed"
    MODAL_CONFIRMED = "modal_confirmed"
    MODAL_CANCELLED = "modal_cancelled"
    
    # UI Events
    UI_UPDATED = "ui_updated"
    BARS_UPDATED = "bars_updated"
    HIGHLIGHTS_CHANGED = "highlights_changed"
    
    # Action Events
    ACTION_EXECUTED = "action_executed"
    ACTION_FAILED = "action_failed"
    MOVEMENT_EXECUTED = "movement_executed"