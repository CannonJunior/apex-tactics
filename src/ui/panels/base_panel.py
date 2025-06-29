"""
Base Panel Class for Engine-Portable UI Components

Provides abstract foundation for game UI panels with cross-engine compatibility.
Supports Ursina, Unity, Godot through consistent interface.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass

try:
    from ursina import Entity, Text, Button, color, camera
    from ursina.prefabs.window_panel import WindowPanel
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False


@dataclass
class PanelConfig:
    """Configuration for panel appearance and behavior."""
    title: str = "Panel"
    width: float = 0.4
    height: float = 0.6
    x_position: float = 0.3
    y_position: float = 0.1
    z_layer: int = 1
    visible: bool = False
    resizable: bool = False
    background_color: tuple = (0.1, 0.1, 0.1, 0.9)


class BasePanel(ABC):
    """
    Abstract base class for all game UI panels.
    
    Provides common functionality:
    - Show/hide management
    - Position and sizing
    - Engine abstraction layer
    - Event handling framework
    """
    
    def __init__(self, config: PanelConfig, game_reference: Optional[Any] = None):
        """
        Initialize base panel.
        
        Args:
            config: Panel configuration settings
            game_reference: Reference to main game object
        """
        self.config = config
        self.game_reference = game_reference
        self.is_visible = False  # Force default to False (hidden)
        self.panel_entity = None
        self.content_elements = []
        
        # Initialize engine-specific implementation
        self._initialize_engine_components()
        
        # Create panel content
        self._create_content()
        
        # Set initial visibility (always hidden by default)
        self.set_visible(False)
    
    def _initialize_engine_components(self):
        """Initialize engine-specific UI components."""
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for BasePanel")
        
        # Create main panel container for Ursina
        self._create_ursina_panel()
    
    def _create_ursina_panel(self):
        """Create Ursina-specific panel implementation."""
        # Create background panel
        self.panel_entity = Entity(
            parent=camera.ui,
            model='cube',
            color=self.config.background_color,
            scale=(self.config.width, self.config.height, 0.01),
            position=(
                self.config.x_position - 0.5,  # Convert to Ursina screen space (-0.5 to 0.5)
                self.config.y_position - 0.5,
                self.config.z_layer * 0.01
            ),
            enabled=False  # Start disabled (hidden)
        )
        
        # Create title if specified
        if self.config.title:
            title_text = Text(
                text=self.config.title,
                parent=self.panel_entity,
                position=(0, self.config.height/2 - 0.05, -0.01),
                scale=1.5,
                color=color.white,
                enabled=False  # Start disabled (hidden)
            )
            self.content_elements.append(title_text)
    
    @abstractmethod
    def _create_content(self):
        """Create panel-specific content. Must be implemented by subclasses."""
        pass
    
    def show(self):
        """Show the panel."""
        self.set_visible(True)
    
    def hide(self):
        """Hide the panel."""
        self.set_visible(False)
    
    def toggle(self):
        """Toggle panel visibility."""
        self.set_visible(not self.is_visible)
    
    def set_visible(self, visible: bool):
        """
        Set panel visibility.
        
        Args:
            visible: True to show, False to hide
        """
        self.is_visible = visible
        
        if self.panel_entity:
            self.panel_entity.enabled = visible
        
        # Update content elements
        for element in self.content_elements:
            if hasattr(element, 'enabled'):
                element.enabled = visible
    
    def update_content(self, data: Dict[str, Any]):
        """
        Update panel content with new data.
        
        Args:
            data: Dictionary containing updated data
        """
        # Default implementation - subclasses should override
        pass
    
    def cleanup(self):
        """Clean up panel resources."""
        if self.panel_entity:
            if hasattr(self.panel_entity, 'enabled'):
                self.panel_entity.enabled = False
            
        for element in self.content_elements:
            if hasattr(element, 'enabled'):
                element.enabled = False
        
        self.content_elements.clear()
    
    def add_text_element(self, text: str, position: tuple, scale: float = 1.0, text_color=None) -> Any:
        """
        Add text element to panel.
        
        Args:
            text: Text content
            position: (x, y, z) position relative to panel
            scale: Text scale factor
            text_color: Text color (defaults to white)
            
        Returns:
            Text element reference
        """
        if text_color is None:
            text_color = color.white
            
        text_element = Text(
            text=text,
            parent=self.panel_entity,
            position=position,
            scale=scale,
            color=text_color,
            enabled=False  # Start disabled (hidden) - will be enabled when panel is shown
        )
        
        self.content_elements.append(text_element)
        return text_element
    
    def add_button_element(self, text: str, position: tuple, size: tuple, 
                          callback: Optional[Callable] = None, button_color=None) -> Any:
        """
        Add button element to panel.
        
        Args:
            text: Button text
            position: (x, y, z) position relative to panel
            size: (width, height) button size
            callback: Click callback function
            button_color: Button color (defaults to gray)
            
        Returns:
            Button element reference
        """
        if button_color is None:
            button_color = color.gray
            
        button = Button(
            text=text,
            parent=self.panel_entity,
            position=position,
            scale=size,
            color=button_color,
            enabled=False  # Start disabled (hidden) - will be enabled when panel is shown
        )
        
        if callback:
            button.on_click = callback
            
        self.content_elements.append(button)
        return button


class PanelManager:
    """
    Manager class for coordinating multiple panels.
    
    Handles:
    - Panel registration and lookup
    - Keyboard shortcuts
    - Panel state management
    - Exclusive panel display logic
    """
    
    def __init__(self):
        """Initialize panel manager."""
        self.panels: Dict[str, BasePanel] = {}
        self.active_panel: Optional[str] = None
        self.key_bindings: Dict[str, str] = {}
    
    def register_panel(self, name: str, panel: BasePanel, toggle_key: Optional[str] = None):
        """
        Register a panel with the manager.
        
        Args:
            name: Unique panel identifier
            panel: Panel instance
            toggle_key: Keyboard key for toggling panel
        """
        self.panels[name] = panel
        
        if toggle_key:
            self.key_bindings[toggle_key] = name
    
    def show_panel(self, name: str):
        """
        Show specific panel (hides others if exclusive).
        
        Args:
            name: Panel name to show
        """
        if name not in self.panels:
            return
        
        # Hide current active panel
        if self.active_panel and self.active_panel != name:
            self.panels[self.active_panel].hide()
        
        # Show requested panel
        self.panels[name].show()
        self.active_panel = name
    
    def hide_panel(self, name: str):
        """
        Hide specific panel.
        
        Args:
            name: Panel name to hide
        """
        if name in self.panels:
            self.panels[name].hide()
            if self.active_panel == name:
                self.active_panel = None
    
    def toggle_panel(self, name: str):
        """
        Toggle specific panel visibility.
        
        Args:
            name: Panel name to toggle
        """
        if name not in self.panels:
            return
            
        if self.panels[name].is_visible:
            self.hide_panel(name)
        else:
            self.show_panel(name)
    
    def handle_key_input(self, key: str) -> bool:
        """
        Handle keyboard input for panel toggles.
        
        Args:
            key: Pressed key
            
        Returns:
            True if key was handled, False otherwise
        """
        if key in self.key_bindings:
            panel_name = self.key_bindings[key]
            self.toggle_panel(panel_name)
            return True
        return False
    
    def update_all_panels(self, data: Dict[str, Any]):
        """
        Update all registered panels with new data.
        
        Args:
            data: Data dictionary for panel updates
        """
        for panel in self.panels.values():
            panel.update_content(data)
    
    def cleanup_all(self):
        """Clean up all managed panels."""
        for panel in self.panels.values():
            panel.cleanup()
        
        self.panels.clear()
        self.key_bindings.clear()
        self.active_panel = None