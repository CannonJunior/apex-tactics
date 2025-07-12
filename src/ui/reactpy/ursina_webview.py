"""
Ursina WebView Integration for ReactPy

Embeds ReactPy components within the Ursina UI using a web view overlay.
This allows ReactPy components to appear as part of the Ursina interface.
"""

try:
    from ursina import Entity, color, destroy, camera, window
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False

import threading
import time
import webbrowser
from typing import Optional, Tuple


class UrsinaReactPyWebView:
    """
    Embeds ReactPy components within Ursina using a transparent web view overlay.
    
    This creates an invisible web browser overlay on top of the Ursina window
    that displays ReactPy components, making them appear as part of the Ursina UI.
    """
    
    def __init__(self, game_controller, reactpy_port: int = 8080):
        if not URSINA_AVAILABLE:
            raise ImportError("Ursina is required for UrsinaReactPyWebView")
            
        self.game_controller = game_controller
        self.reactpy_port = reactpy_port
        self.is_running = False
        self.server_thread: Optional[threading.Thread] = None
        
    def start_embedded_reactpy(self):
        """Start ReactPy server and create embedded web view"""
        print("🌐 Starting embedded ReactPy in Ursina...")
        
        # Start ReactPy server in background
        self.server_thread = threading.Thread(target=self._start_reactpy_server, daemon=True)
        self.server_thread.start()
        
        # Wait a moment for server to start
        time.sleep(2)
        
        # Create embedded web view entity
        self._create_web_view_entity()
        
        self.is_running = True
        print("✅ Embedded ReactPy started in Ursina")
    
    def _start_reactpy_server(self):
        """Start the ReactPy server in background"""
        try:
            from .app import start_reactpy_server
            start_reactpy_server(self.reactpy_port)
        except Exception as e:
            print(f"❌ Failed to start ReactPy server: {e}")
    
    def _create_web_view_entity(self):
        """Create Ursina entity that displays ReactPy web view"""
        # For now, create a simple button that opens ReactPy in browser
        # This is a temporary solution until proper web view integration
        
        from ursina import Button, Text
        
        # Get master UI config for positioning
        try:
            from src.core.ui.ui_config_manager import get_ui_config_manager
            ui_config = get_ui_config_manager()
            
            # Get end turn button position and offset it
            end_turn_pos = ui_config.get('panels.control_panel.end_turn_button.position', {})
            reactpy_pos = {
                'x': end_turn_pos.get('x', -0.7),
                'y': end_turn_pos.get('y', 0.3) - 0.15,  # Position below Ursina button
                'z': end_turn_pos.get('z', 0.01)
            }
            
            button_color = ui_config.get_color('panels.control_panel.end_turn_button.color', '#FFA500')
            button_scale = ui_config.get('panels.control_panel.end_turn_button.scale', 0.08)
            
        except ImportError:
            # Fallback positioning
            reactpy_pos = {'x': -0.7, 'y': 0.15, 'z': 0.01}
            button_color = color.orange
            button_scale = 0.08
        
        # Create ReactPy End Turn Button
        self.reactpy_button = Button(
            text='End Turn (ReactPy)',
            position=(reactpy_pos['x'], reactpy_pos['y'], reactpy_pos['z']),
            scale=button_scale,
            color=button_color,
            on_click=self._handle_reactpy_button_click
        )
        
        # Add visual indicator that this is ReactPy
        self.reactpy_label = Text(
            'ReactPy',
            position=(reactpy_pos['x'], reactpy_pos['y'] - 0.08, reactpy_pos['z']),
            scale=0.5,
            color=color.white,
            parent=self.reactpy_button
        )
        
        print(f"📱 ReactPy button created at position {reactpy_pos}")
    
    def _handle_reactpy_button_click(self):
        """Handle ReactPy button click - same functionality as Ursina button"""
        print("🎮 ReactPy End Turn button clicked!")
        
        # Call the same end_turn function as the Ursina button
        if hasattr(self.game_controller, 'control_panel') and self.game_controller.control_panel:
            print("📞 Calling game controller end_turn_clicked")
            self.game_controller.control_panel.end_turn_clicked()
        else:
            print("⚠️ No control panel available for end turn")
    
    def open_reactpy_browser(self):
        """Open ReactPy interface in external browser for testing"""
        url = f"http://localhost:{self.reactpy_port}"
        print(f"🌐 Opening ReactPy interface: {url}")
        webbrowser.open(url)
    
    def stop_embedded_reactpy(self):
        """Stop the embedded ReactPy integration"""
        self.is_running = False
        
        # Destroy Ursina entities
        if hasattr(self, 'reactpy_button'):
            destroy(self.reactpy_button)
        if hasattr(self, 'reactpy_label'):
            destroy(self.reactpy_label)
        
        print("🛑 Embedded ReactPy stopped")


def create_embedded_reactpy(game_controller) -> Optional[UrsinaReactPyWebView]:
    """
    Create embedded ReactPy integration for Ursina.
    
    Returns:
        UrsinaReactPyWebView instance or None if creation fails
    """
    try:
        webview = UrsinaReactPyWebView(game_controller)
        webview.start_embedded_reactpy()
        return webview
    except Exception as e:
        print(f"⚠️ Failed to create embedded ReactPy: {e}")
        return None