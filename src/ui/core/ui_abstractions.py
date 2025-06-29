"""
Portable UI Architecture Abstractions

Provides engine-agnostic interface layer for UI components that can be ported 
between Ursina, Unity, Godot, and other engines.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Tuple
from enum import Enum
from dataclasses import dataclass, field

# Color and styling abstractions
@dataclass
class UIColor:
    """Engine-agnostic color representation"""
    r: float  # 0.0 to 1.0
    g: float  # 0.0 to 1.0  
    b: float  # 0.0 to 1.0
    a: float = 1.0  # Alpha
    
    @classmethod
    def from_hex(cls, hex_str: str) -> 'UIColor':
        """Create color from hex string like '#FF0000'"""
        hex_str = hex_str.lstrip('#')
        r = int(hex_str[0:2], 16) / 255.0
        g = int(hex_str[2:4], 16) / 255.0
        b = int(hex_str[4:6], 16) / 255.0
        return cls(r, g, b)
    
    @classmethod
    def white(cls) -> 'UIColor':
        return cls(1.0, 1.0, 1.0)
    
    @classmethod
    def black(cls) -> 'UIColor':
        return cls(0.0, 0.0, 0.0)
    
    @classmethod
    def gray(cls, value: float = 0.5) -> 'UIColor':
        return cls(value, value, value)

@dataclass
class UIVector2:
    """Engine-agnostic 2D vector for positions and sizes"""
    x: float
    y: float
    
    def __add__(self, other: 'UIVector2') -> 'UIVector2':
        return UIVector2(self.x + other.x, self.y + other.y)
    
    def __mul__(self, scalar: float) -> 'UIVector2':
        return UIVector2(self.x * scalar, self.y * scalar)

@dataclass
class UIRect:
    """Engine-agnostic rectangle for UI bounds"""
    position: UIVector2
    size: UIVector2
    
    @property
    def center(self) -> UIVector2:
        return UIVector2(
            self.position.x + self.size.x / 2,
            self.position.y + self.size.y / 2
        )

class UIAnchor(Enum):
    """UI element anchoring modes"""
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"

class UILayoutMode(Enum):
    """Layout arrangement modes"""
    ABSOLUTE = "absolute"        # Fixed positions
    VERTICAL = "vertical"        # Vertical stack
    HORIZONTAL = "horizontal"    # Horizontal row
    GRID = "grid"               # Grid arrangement
    FLOW = "flow"               # Flow layout

# Abstract base classes for UI components
class IUIElement(ABC):
    """Base interface for all UI elements"""
    
    def __init__(self, name: str = ""):
        self.name = name
        self.visible = True
        self.enabled = True
        self.position = UIVector2(0, 0)
        self.size = UIVector2(100, 100)
        self.anchor = UIAnchor.TOP_LEFT
        self.parent: Optional['IUIElement'] = None
        self.children: List['IUIElement'] = []
        self.event_handlers: Dict[str, List[Callable]] = {}
    
    @abstractmethod
    def render(self) -> None:
        """Render this UI element"""
        pass
    
    @abstractmethod
    def update(self, delta_time: float) -> None:
        """Update this UI element"""
        pass
    
    @abstractmethod
    def destroy(self) -> None:
        """Clean up and destroy this UI element"""
        pass
    
    def add_child(self, child: 'IUIElement') -> None:
        """Add a child element"""
        child.parent = self
        self.children.append(child)
    
    def remove_child(self, child: 'IUIElement') -> None:
        """Remove a child element"""
        if child in self.children:
            child.parent = None
            self.children.remove(child)
    
    def add_event_handler(self, event_type: str, handler: Callable) -> None:
        """Add event handler for specific event type"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def trigger_event(self, event_type: str, *args, **kwargs) -> None:
        """Trigger event handlers for specific event type"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(*args, **kwargs)
                except Exception as e:
                    print(f"Error in UI event handler: {e}")

class IUIButton(IUIElement):
    """Abstract button interface"""
    
    def __init__(self, text: str = "", on_click: Optional[Callable] = None):
        super().__init__()
        self.text = text
        self.background_color = UIColor.gray(0.7)
        self.text_color = UIColor.black()
        self.hover_color = UIColor.gray(0.8)
        self.pressed_color = UIColor.gray(0.6)
        self.is_hovered = False
        self.is_pressed = False
        
        if on_click:
            self.add_event_handler("click", on_click)
    
    @abstractmethod
    def set_text(self, text: str) -> None:
        """Set button text"""
        pass

class IUIPanel(IUIElement):
    """Abstract panel interface"""
    
    def __init__(self, background_color: UIColor = UIColor.gray(0.9)):
        super().__init__()
        self.background_color = background_color
        self.border_color = UIColor.gray(0.5)
        self.border_width = 1.0
        self.layout_mode = UILayoutMode.ABSOLUTE
        self.padding = UIVector2(10, 10)
    
    @abstractmethod
    def set_background_color(self, color: UIColor) -> None:
        """Set panel background color"""
        pass

class IUIText(IUIElement):
    """Abstract text label interface"""
    
    def __init__(self, text: str = "", color: UIColor = UIColor.black()):
        super().__init__()
        self.text = text
        self.color = color
        self.font_size = 16
        self.alignment = UIAnchor.CENTER_LEFT
    
    @abstractmethod
    def set_text(self, text: str) -> None:
        """Set text content"""
        pass
    
    @abstractmethod
    def set_font_size(self, size: int) -> None:
        """Set font size"""
        pass

class IUIScreen(IUIElement):
    """Abstract screen/window interface"""
    
    def __init__(self, title: str = ""):
        super().__init__()
        self.title = title
        self.is_modal = False
        self.can_close = True
        self.is_active = False
    
    @abstractmethod
    def show(self) -> None:
        """Show this screen"""
        pass
    
    @abstractmethod
    def hide(self) -> None:
        """Hide this screen"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close this screen"""
        pass

# UI Manager interface
class IUIManager(ABC):
    """Abstract UI manager for engine-specific implementations"""
    
    @abstractmethod
    def create_button(self, text: str, position: UIVector2, size: UIVector2) -> IUIButton:
        """Create a button element"""
        pass
    
    @abstractmethod
    def create_panel(self, position: UIVector2, size: UIVector2) -> IUIPanel:
        """Create a panel element"""
        pass
    
    @abstractmethod
    def create_text(self, text: str, position: UIVector2) -> IUIText:
        """Create a text element"""
        pass
    
    @abstractmethod
    def create_screen(self, title: str) -> IUIScreen:
        """Create a screen/window"""
        pass
    
    @abstractmethod
    def update(self, delta_time: float) -> None:
        """Update UI system"""
        pass
    
    @abstractmethod
    def render(self) -> None:
        """Render UI system"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup UI system"""
        pass

# Event system for UI
@dataclass
class UIEvent:
    """UI event data structure"""
    event_type: str
    source: IUIElement
    data: Dict[str, Any] = field(default_factory=dict)

class UIEventBus:
    """Event bus for UI system communication"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to UI events"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Unsubscribe from UI events"""
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(callback)
            except ValueError:
                pass
    
    def publish(self, event: UIEvent) -> None:
        """Publish UI event"""
        if event.event_type in self.subscribers:
            for callback in self.subscribers[event.event_type]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error in UI event subscriber: {e}")

# Theme and styling system
@dataclass
class UITheme:
    """UI theme configuration"""
    primary_color: UIColor = field(default_factory=lambda: UIColor.from_hex("#2196F3"))
    secondary_color: UIColor = field(default_factory=lambda: UIColor.from_hex("#FFC107"))
    background_color: UIColor = field(default_factory=lambda: UIColor.gray(0.95))
    text_color: UIColor = field(default_factory=lambda: UIColor.black())
    button_color: UIColor = field(default_factory=lambda: UIColor.gray(0.8))
    button_hover_color: UIColor = field(default_factory=lambda: UIColor.gray(0.9))
    button_pressed_color: UIColor = field(default_factory=lambda: UIColor.gray(0.7))
    panel_color: UIColor = field(default_factory=lambda: UIColor.gray(0.9))
    border_color: UIColor = field(default_factory=lambda: UIColor.gray(0.6))
    
    @classmethod
    def dark_theme(cls) -> 'UITheme':
        """Create dark theme variant"""
        return cls(
            primary_color=UIColor.from_hex("#1976D2"),
            secondary_color=UIColor.from_hex("#FFA000"),
            background_color=UIColor.gray(0.15),
            text_color=UIColor.white(),
            button_color=UIColor.gray(0.3),
            button_hover_color=UIColor.gray(0.4),
            button_pressed_color=UIColor.gray(0.2),
            panel_color=UIColor.gray(0.2),
            border_color=UIColor.gray(0.5)
        )

# Global UI state management
class UIState:
    """Global UI state manager"""
    
    def __init__(self):
        self.current_screen: Optional[IUIScreen] = None
        self.screen_stack: List[IUIScreen] = []
        self.theme = UITheme()
        self.event_bus = UIEventBus()
        self.ui_manager: Optional[IUIManager] = None
    
    def set_ui_manager(self, manager: IUIManager) -> None:
        """Set the engine-specific UI manager"""
        self.ui_manager = manager
    
    def push_screen(self, screen: IUIScreen) -> None:
        """Push a new screen onto the stack"""
        if self.current_screen:
            self.screen_stack.append(self.current_screen)
            self.current_screen.hide()
        
        self.current_screen = screen
        screen.show()
    
    def pop_screen(self) -> Optional[IUIScreen]:
        """Pop the current screen and return to previous"""
        if self.current_screen:
            self.current_screen.close()
        
        popped_screen = self.current_screen
        
        if self.screen_stack:
            self.current_screen = self.screen_stack.pop()
            self.current_screen.show()
        else:
            self.current_screen = None
        
        return popped_screen
    
    def set_theme(self, theme: UITheme) -> None:
        """Set the UI theme"""
        self.theme = theme
        self.event_bus.publish(UIEvent("theme_changed", None, {"theme": theme}))

# Global instance
ui_state = UIState()