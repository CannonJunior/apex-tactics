"""
Ursina Implementation of Portable UI System

Provides Ursina-specific implementations of the abstract UI interfaces.
"""

from typing import Optional, Dict, Any
import math

try:
    from ursina import *
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False

from ..core.ui_abstractions import *

class UrsinaUIButton(IUIButton):
    """Ursina implementation of UI button"""
    
    def __init__(self, text: str = "", on_click: Optional[Callable] = None):
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for UrsinaUIButton")
        
        super().__init__(text, on_click)
        
        # Load master UI configuration for buttons
        try:
            from src.core.ui.ui_config_manager import get_ui_config_manager
            ui_config = get_ui_config_manager()
            
            # Button configuration from master UI config
            button_config = ui_config.get('ui_ursina.button', {})
            default_scale = button_config.get('default_scale', (0.2, 0.1))
            default_background_color = ui_config.get_color('ui_ursina.button.background_color', '#D3D3D3')
            default_text_color = ui_config.get_color('ui_ursina.button.text_color', '#000000')
            ui_parent = button_config.get('parent', 'camera.ui')
        except ImportError:
            # Fallback values if master UI config not available
            default_scale = (0.2, 0.1)
            default_background_color = self.background_color
            default_text_color = self.text_color
            ui_parent = 'camera.ui'
        
        # Use master UI config values or fallbacks
        button_scale = (self.size.x / 100, self.size.y / 100) if hasattr(self, 'size') else default_scale
        button_bg_color = self._convert_color(self.background_color) if hasattr(self, 'background_color') else self._convert_color(default_background_color)
        button_text_color = self._convert_color(self.text_color) if hasattr(self, 'text_color') else self._convert_color(default_text_color)
        
        # Create Ursina button entity with proper UI parenting
        # Note: Ursina UI Y coordinate is inverted (0.5 at top, -0.5 at bottom)
        self.entity = Button(
            text=self.text,
            scale=button_scale,
            position=(self.position.x / 100 - 0.5, 0.5 - self.position.y / 100) if hasattr(self, 'position') else (0, 0),
            color=button_bg_color,
            text_color=button_text_color,
            on_click=self._handle_click,
            parent=camera.ui
        )
        
        # Store original color states
        self._default_color = self.entity.color
        self._hover_color = self._convert_color(self.hover_color)
        self._pressed_color = self._convert_color(self.pressed_color)
        
        # Set up hover events
        self.entity.on_mouse_enter = self._handle_mouse_enter
        self.entity.on_mouse_exit = self._handle_mouse_exit
    
    def _convert_color(self, ui_color) -> Any:
        """Convert UIColor to Ursina color with master UI config support"""
        # Handle both UIColor objects and direct Ursina colors from master UI config
        if hasattr(ui_color, 'r') and hasattr(ui_color, 'g') and hasattr(ui_color, 'b'):
            # UIColor object
            return color.rgb(ui_color.r * 255, ui_color.g * 255, ui_color.b * 255)
        else:
            # Already a Ursina color from master UI config
            return ui_color
    
    def _handle_click(self):
        """Handle button click"""
        self.trigger_event("click", self)
    
    def _handle_mouse_enter(self):
        """Handle mouse enter"""
        self.is_hovered = True
        self.entity.color = self._hover_color
        self.trigger_event("hover_enter", self)
    
    def _handle_mouse_exit(self):
        """Handle mouse exit"""
        self.is_hovered = False
        self.entity.color = self._default_color
        self.trigger_event("hover_exit", self)
    
    def set_text(self, text: str) -> None:
        """Set button text"""
        self.text = text
        if self.entity:
            self.entity.text = text
    
    def render(self) -> None:
        """Render button (handled by Ursina)"""
        if self.entity:
            self.entity.enabled = self.visible and self.enabled
    
    def update(self, delta_time: float) -> None:
        """Update button"""
        # Update position and scale if changed
        if self.entity:
            # Convert from 0-100 percentage to Ursina UI coordinates with inverted Y
            self.entity.position = (
                (self.position.x / 100) - 0.5, 
                0.5 - (self.position.y / 100)
            )
            self.entity.scale = (self.size.x / 100, self.size.y / 100)
    
    def destroy(self) -> None:
        """Destroy button"""
        if self.entity:
            destroy(self.entity)
            self.entity = None

class UrsinaUIPanel(IUIPanel):
    """Ursina implementation of UI panel"""
    
    def __init__(self, background_color = None):
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for UrsinaUIPanel")
        
        # Load master UI configuration for panels
        try:
            from src.core.ui.ui_config_manager import get_ui_config_manager
            ui_config = get_ui_config_manager()
            
            # Panel configuration from master UI config
            panel_config = ui_config.get('ui_ursina.panel', {})
            default_background_color = ui_config.get_color('ui_ursina.panel.background_color', '#E6E6E6')
            default_model = panel_config.get('model', 'quad')
            default_scale = panel_config.get('default_scale', (0.5, 0.5))
            ui_parent = panel_config.get('parent', 'camera.ui')
        except ImportError:
            # Fallback values if master UI config not available
            default_background_color = UIColor.gray(0.9) if 'UIColor' in globals() else None
            default_model = 'quad'
            default_scale = (0.5, 0.5)
            ui_parent = 'camera.ui'
        
        # Use provided background color or default from master UI config
        if background_color is None:
            background_color = default_background_color
        
        super().__init__(background_color)
        
        # Use master UI config values or fallbacks
        panel_scale = (self.size.x / 100, self.size.y / 100) if hasattr(self, 'size') else default_scale
        panel_color = self._convert_color(self.background_color) if hasattr(self, 'background_color') else self._convert_color(default_background_color)
        
        # Create Ursina panel entity using quad for 2D UI
        # Note: Ursina UI Y coordinate is inverted (0.5 at top, -0.5 at bottom)
        self.entity = Entity(
            model=default_model,
            color=panel_color,
            scale=panel_scale,
            position=(self.position.x / 100 - 0.5, 0.5 - self.position.y / 100) if hasattr(self, 'position') else (0, 0),
            parent=camera.ui
        )
        
        # Create border if needed
        self.border_entity = None
        if self.border_width > 0:
            self._create_border()
    
    def _convert_color(self, ui_color) -> Any:
        """Convert UIColor to Ursina color with master UI config support"""
        # Handle both UIColor objects and direct Ursina colors from master UI config
        if hasattr(ui_color, 'r') and hasattr(ui_color, 'g') and hasattr(ui_color, 'b'):
            # UIColor object
            return color.rgb(ui_color.r * 255, ui_color.g * 255, ui_color.b * 255)
        else:
            # Already a Ursina color from master UI config
            return ui_color
    
    def _create_border(self):
        """Create border around panel"""
        border_color = self._convert_color(self.border_color)
        border_scale = (
            (self.size.x + self.border_width * 2) / 100,
            (self.size.y + self.border_width * 2) / 100
        )
        
        self.border_entity = Entity(
            model='quad',
            color=border_color,
            scale=border_scale,
            position=self.entity.position,
            parent=camera.ui
        )
    
    def set_background_color(self, color: UIColor) -> None:
        """Set panel background color"""
        self.background_color = color
        if self.entity:
            self.entity.color = self._convert_color(color)
    
    def render(self) -> None:
        """Render panel (handled by Ursina)"""
        if self.entity:
            self.entity.enabled = self.visible
        if self.border_entity:
            self.border_entity.enabled = self.visible
    
    def update(self, delta_time: float) -> None:
        """Update panel"""
        if self.entity:
            # Convert from 0-100 percentage to Ursina UI coordinates with inverted Y
            self.entity.position = (
                (self.position.x / 100) - 0.5, 
                0.5 - (self.position.y / 100)
            )
            self.entity.scale = (self.size.x / 100, self.size.y / 100)
        
        if self.border_entity:
            self.border_entity.position = self.entity.position
            border_scale = (
                (self.size.x + self.border_width * 2) / 100,
                (self.size.y + self.border_width * 2) / 100
            )
            self.border_entity.scale = border_scale
    
    def destroy(self) -> None:
        """Destroy panel"""
        if self.entity:
            destroy(self.entity)
            self.entity = None
        if self.border_entity:
            destroy(self.border_entity)
            self.border_entity = None

class UrsinaUIText(IUIText):
    """Ursina implementation of UI text"""
    
    def __init__(self, text: str = "", color = None):
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for UrsinaUIText")
        
        # Load master UI configuration for text
        try:
            from src.core.ui.ui_config_manager import get_ui_config_manager
            ui_config = get_ui_config_manager()
            
            # Text configuration from master UI config
            text_config = ui_config.get('ui_ursina.text', {})
            default_color = ui_config.get_color('ui_ursina.text.color', '#000000')
            default_font_size = text_config.get('default_font_size', 16)
            default_scale_ratio = text_config.get('scale_ratio', 16.0)
            ui_parent = text_config.get('parent', 'camera.ui')
        except ImportError:
            # Fallback values if master UI config not available
            default_color = UIColor.black() if 'UIColor' in globals() else None
            default_font_size = 16
            default_scale_ratio = 16.0
            ui_parent = 'camera.ui'
        
        # Use provided color or default from master UI config
        if color is None:
            color = default_color
        
        super().__init__(text, color)
        
        # Use master UI config values or fallbacks
        text_color = self._convert_color(self.color) if hasattr(self, 'color') else self._convert_color(default_color)
        text_scale = (self.font_size / default_scale_ratio) if hasattr(self, 'font_size') else (default_font_size / default_scale_ratio)
        
        # Create Ursina text entity with proper UI parenting
        # Note: Ursina UI Y coordinate is inverted (0.5 at top, -0.5 at bottom)
        self.entity = Text(
            text=self.text,
            position=(self.position.x / 100 - 0.5, 0.5 - self.position.y / 100) if hasattr(self, 'position') else (0, 0),
            color=text_color,
            scale=text_scale,
            parent=camera.ui
        )
    
    def _convert_color(self, ui_color) -> Any:
        """Convert UIColor to Ursina color with master UI config support"""
        # Handle both UIColor objects and direct Ursina colors from master UI config
        if hasattr(ui_color, 'r') and hasattr(ui_color, 'g') and hasattr(ui_color, 'b'):
            # UIColor object
            return color.rgb(ui_color.r * 255, ui_color.g * 255, ui_color.b * 255)
        else:
            # Already a Ursina color from master UI config
            return ui_color
    
    def set_text(self, text: str) -> None:
        """Set text content"""
        self.text = text
        if self.entity:
            self.entity.text = text
    
    def set_font_size(self, size: int) -> None:
        """Set font size"""
        self.font_size = size
        if self.entity:
            self.entity.scale = size / 16.0
    
    def render(self) -> None:
        """Render text (handled by Ursina)"""
        if self.entity:
            self.entity.enabled = self.visible
    
    def update(self, delta_time: float) -> None:
        """Update text"""
        if self.entity:
            # Convert from 0-100 percentage to Ursina UI coordinates with inverted Y
            self.entity.position = (
                (self.position.x / 100) - 0.5, 
                0.5 - (self.position.y / 100)
            )
    
    def destroy(self) -> None:
        """Destroy text"""
        if self.entity:
            destroy(self.entity)
            self.entity = None

class UrsinaUIScreen(IUIScreen):
    """Ursina implementation of UI screen"""
    
    def __init__(self, title: str = ""):
        super().__init__(title)
        self.background_panel: Optional[UrsinaUIPanel] = None
        self.title_text: Optional[UrsinaUIText] = None
        
        # Create screen background
        self._create_background()
        
        # Create title if provided
        if self.title:
            self._create_title()
    
    def _create_background(self):
        """Create screen background panel using master UI config"""
        try:
            from src.core.ui.ui_config_manager import get_ui_config_manager
            ui_config = get_ui_config_manager()
            
            # Screen background configuration from master UI config
            screen_config = ui_config.get('ui_ursina.screen.background', {})
            bg_color = ui_config.get_color('ui_ursina.screen.background.color', '#F2F2F2')
            bg_position = screen_config.get('position', {'x': 0, 'y': 0})
            bg_size = screen_config.get('size', {'x': 100, 'y': 100})
        except ImportError:
            # Fallback values if master UI config not available
            bg_color = UIColor.gray(0.95) if 'UIColor' in globals() else None
            bg_position = {'x': 0, 'y': 0}
            bg_size = {'x': 100, 'y': 100}
        
        self.background_panel = UrsinaUIPanel(bg_color)
        if hasattr(self.background_panel, 'position'):
            self.background_panel.position = UIVector2(bg_position['x'], bg_position['y']) if 'UIVector2' in globals() else None
        if hasattr(self.background_panel, 'size'):
            self.background_panel.size = UIVector2(bg_size['x'], bg_size['y']) if 'UIVector2' in globals() else None
        self.add_child(self.background_panel)
    
    def _create_title(self):
        """Create title text using master UI config"""
        try:
            from src.core.ui.ui_config_manager import get_ui_config_manager
            ui_config = get_ui_config_manager()
            
            # Title configuration from master UI config
            title_config = ui_config.get('ui_ursina.screen.title', {})
            title_color = ui_config.get_color('ui_ursina.screen.title.color', '#000000')
            title_position = title_config.get('position', {'x': 50, 'y': 90})
            title_font_size = title_config.get('font_size', 24)
        except ImportError:
            # Fallback values if master UI config not available
            title_color = UIColor.black() if 'UIColor' in globals() else None
            title_position = {'x': 50, 'y': 90}
            title_font_size = 24
        
        self.title_text = UrsinaUIText(self.title, title_color)
        if hasattr(self.title_text, 'position'):
            self.title_text.position = UIVector2(title_position['x'], title_position['y']) if 'UIVector2' in globals() else None
        if hasattr(self.title_text, 'font_size'):
            self.title_text.font_size = title_font_size
        self.add_child(self.title_text)
    
    def show(self) -> None:
        """Show this screen"""
        self.is_active = True
        self.visible = True
        for child in self.children:
            child.visible = True
            child.render()
    
    def hide(self) -> None:
        """Hide this screen"""
        self.is_active = False
        self.visible = False
        for child in self.children:
            child.visible = False
            child.render()
    
    def close(self) -> None:
        """Close this screen"""
        self.hide()
        self.destroy()
    
    def render(self) -> None:
        """Render screen and all children"""
        for child in self.children:
            child.render()
    
    def update(self, delta_time: float) -> None:
        """Update screen and all children"""
        for child in self.children:
            child.update(delta_time)
    
    def destroy(self) -> None:
        """Destroy screen and all children"""
        for child in self.children[:]:  # Copy list to avoid modification during iteration
            child.destroy()
            self.remove_child(child)

class UrsinaUIManager(IUIManager):
    """Ursina implementation of UI manager"""
    
    def __init__(self):
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for UrsinaUIManager")
        
        # Load master UI configuration for manager
        try:
            from src.core.ui.ui_config_manager import get_ui_config_manager
            self.ui_config = get_ui_config_manager()
            
            # Manager configuration from master UI config
            manager_config = self.ui_config.get('ui_ursina.manager', {})
            self.default_update_interval = manager_config.get('update_interval', 0.016)  # ~60 FPS
            self.enable_auto_cleanup = manager_config.get('enable_auto_cleanup', True)
            self.max_elements = manager_config.get('max_elements', 1000)
        except ImportError:
            # Fallback values if master UI config not available
            self.ui_config = None
            self.default_update_interval = 0.016
            self.enable_auto_cleanup = True
            self.max_elements = 1000
        
        self.elements: List[IUIElement] = []
    
    def create_button(self, text: str, position: UIVector2, size: UIVector2) -> IUIButton:
        """Create a button element"""
        button = UrsinaUIButton(text)
        button.position = position
        button.size = size
        self.elements.append(button)
        return button
    
    def create_panel(self, position: UIVector2, size: UIVector2) -> IUIPanel:
        """Create a panel element"""
        panel = UrsinaUIPanel()
        panel.position = position
        panel.size = size
        self.elements.append(panel)
        return panel
    
    def create_text(self, text: str, position: UIVector2) -> IUIText:
        """Create a text element"""
        text_element = UrsinaUIText(text)
        text_element.position = position
        self.elements.append(text_element)
        return text_element
    
    def create_screen(self, title: str) -> IUIScreen:
        """Create a screen/window"""
        screen = UrsinaUIScreen(title)
        self.elements.append(screen)
        return screen
    
    def update(self, delta_time: float) -> None:
        """Update UI system"""
        for element in self.elements:
            if element.enabled:
                element.update(delta_time)
    
    def render(self) -> None:
        """Render UI system"""
        for element in self.elements:
            if element.visible:
                element.render()
    
    def cleanup(self) -> None:
        """Cleanup UI system"""
        for element in self.elements[:]:
            element.destroy()
        self.elements.clear()
    
    def remove_element(self, element: IUIElement) -> None:
        """Remove element from manager"""
        if element in self.elements:
            element.destroy()
            self.elements.remove(element)