"""
ReactPy End Turn Button Component

ReactPy implementation of the End Turn button that matches the Ursina version
and uses the same master UI configuration.
"""

from reactpy import component, html, hooks
from typing import Optional

from ..config_loader import get_reactpy_config
from ..bridge.game_bridge import GameBridge


@component
def EndTurnButton(game_bridge: Optional[GameBridge] = None):
    """
    ReactPy End Turn Button Component
    
    Renders an end turn button positioned below the Ursina button
    using configuration from master_ui_config.json
    """
    
    # Load configuration
    config = get_reactpy_config()
    
    # Get button configuration from master UI config
    button_config_path = "panels.control_panel.end_turn_button"
    
    button_text = config.get(f"{button_config_path}.text", "End Turn")
    button_color = config.get_color(f"{button_config_path}.color", "#FFA500")
    text_color = config.get_color(f"{button_config_path}.text_color", "#000000")
    
    # Get position (we'll offset it below the Ursina button)
    ursina_position = config.get_position(f"{button_config_path}.position")
    reactpy_position = {
        "x": ursina_position["x"],
        "y": ursina_position["y"] - 0.15,  # Position below Ursina button
        "z": ursina_position["z"]
    }
    
    # Convert to CSS positioning
    css_position = config.get_css_position(f"{button_config_path}.position")
    css_scale = config.get_css_scale(f"{button_config_path}.scale", 80)
    
    # Adjust CSS position for ReactPy button (below Ursina)
    current_top = float(css_position["top"].replace("px", ""))
    reactpy_css_position = {
        **css_position,
        "top": f"{current_top + 80}px"  # Move down by button height + margin
    }
    
    # State for button interactions
    is_hovered, set_is_hovered = hooks.use_state(False)
    is_pressed, set_is_pressed = hooks.use_state(False)
    
    async def handle_click(event):
        """Handle button click - send to game bridge"""
        print("🎮 ReactPy: End Turn button clicked!")
        
        if game_bridge:
            await game_bridge.send_button_click("end_turn", {
                "source": "reactpy",
                "button_id": "end_turn_reactpy"
            })
        else:
            print("⚠️ ReactPy: No game bridge available")
    
    def handle_mouse_enter(event):
        """Handle mouse enter for hover effect"""
        set_is_hovered(True)
    
    def handle_mouse_leave(event):
        """Handle mouse leave to remove hover effect"""
        set_is_hovered(False)
        set_is_pressed(False)
    
    def handle_mouse_down(event):
        """Handle mouse down for pressed effect"""
        set_is_pressed(True)
    
    def handle_mouse_up(event):
        """Handle mouse up to remove pressed effect"""
        set_is_pressed(False)
    
    # Calculate button style with state effects
    base_opacity = 0.9
    hover_opacity = 1.0
    pressed_scale = 0.95
    
    current_opacity = hover_opacity if is_hovered else base_opacity
    current_scale = pressed_scale if is_pressed else 1.0
    
    button_style = {
        "position": "absolute",
        "left": reactpy_css_position["left"],
        "top": reactpy_css_position["top"],
        "width": css_scale["width"],
        "height": css_scale["height"],
        "background-color": button_color,
        "color": text_color,
        "border": "2px solid #333333",
        "border-radius": "8px",
        "cursor": "pointer",
        "font-family": "Arial, sans-serif",
        "font-size": "14px",
        "font-weight": "bold",
        "display": "flex",
        "align-items": "center",
        "justify-content": "center",
        "opacity": str(current_opacity),
        "transform": f"scale({current_scale})",
        "transition": "all 0.1s ease",
        "pointer-events": "auto",  # Enable clicks for this button
        "z-index": reactpy_css_position["z-index"],
        "box-shadow": "0 2px 4px rgba(0,0,0,0.3)" if is_hovered else "0 1px 2px rgba(0,0,0,0.2)",
        "user-select": "none"
    }
    
    return html.button(
        {
            "style": button_style,
            "on_click": handle_click,
            "on_mouse_enter": handle_mouse_enter,
            "on_mouse_leave": handle_mouse_leave,
            "on_mouse_down": handle_mouse_down,
            "on_mouse_up": handle_mouse_up,
            "title": "End Turn (ReactPy)"  # Tooltip to distinguish from Ursina button
        },
        button_text
    )