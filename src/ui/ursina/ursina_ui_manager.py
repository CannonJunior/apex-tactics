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
        
        # Create Ursina button entity with proper UI parenting
        # Note: Ursina UI Y coordinate is inverted (0.5 at top, -0.5 at bottom)
        self.entity = Button(
            text=self.text,
            scale=(self.size.x / 100, self.size.y / 100),
            position=(self.position.x / 100 - 0.5, 0.5 - self.position.y / 100),
            color=self._convert_color(self.background_color),
            text_color=self._convert_color(self.text_color),
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
    
    def _convert_color(self, ui_color: UIColor) -> Any:
        """Convert UIColor to Ursina color"""
        return color.rgb(ui_color.r * 255, ui_color.g * 255, ui_color.b * 255)
    
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
    
    def __init__(self, background_color: UIColor = UIColor.gray(0.9)):
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for UrsinaUIPanel")
        
        super().__init__(background_color)
        
        # Create Ursina panel entity using quad for 2D UI
        # Note: Ursina UI Y coordinate is inverted (0.5 at top, -0.5 at bottom)
        self.entity = Entity(
            model='quad',
            color=self._convert_color(self.background_color),
            scale=(self.size.x / 100, self.size.y / 100),
            position=(self.position.x / 100 - 0.5, 0.5 - self.position.y / 100),
            parent=camera.ui
        )
        
        # Create border if needed
        self.border_entity = None
        if self.border_width > 0:
            self._create_border()
    
    def _convert_color(self, ui_color: UIColor) -> Any:
        """Convert UIColor to Ursina color"""
        return color.rgb(ui_color.r * 255, ui_color.g * 255, ui_color.b * 255)
    
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
    
    def __init__(self, text: str = "", color: UIColor = UIColor.black()):
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for UrsinaUIText")
        
        super().__init__(text, color)
        
        # Create Ursina text entity with proper UI parenting
        # Note: Ursina UI Y coordinate is inverted (0.5 at top, -0.5 at bottom)
        self.entity = Text(
            text=self.text,
            position=(self.position.x / 100 - 0.5, 0.5 - self.position.y / 100),
            color=self._convert_color(self.color),
            scale=self.font_size / 16.0,  # Scale relative to default
            parent=camera.ui
        )
    
    def _convert_color(self, ui_color: UIColor) -> Any:
        """Convert UIColor to Ursina color"""
        return color.rgb(ui_color.r * 255, ui_color.g * 255, ui_color.b * 255)
    
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
        """Create screen background panel"""
        self.background_panel = UrsinaUIPanel(UIColor.gray(0.95))
        self.background_panel.position = UIVector2(0, 0)
        self.background_panel.size = UIVector2(100, 100)  # Full screen
        self.add_child(self.background_panel)
    
    def _create_title(self):
        """Create title text"""
        self.title_text = UrsinaUIText(self.title, UIColor.black())
        self.title_text.position = UIVector2(50, 90)  # Top center
        self.title_text.font_size = 24
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