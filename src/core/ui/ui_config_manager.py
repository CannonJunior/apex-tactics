"""
UI Configuration Manager

Central manager for loading and accessing all UI configuration data from the master UI config file.
Provides utilities for retrieving colors, positions, scales, and other visual properties.
"""

import json
import os
from typing import Dict, Any, Optional, Tuple, Union
from pathlib import Path

try:
    from ursina import color
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False


class UIConfigManager:
    """Manages loading and accessing UI configuration from master config file."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize UI config manager with path to master config file."""
        if config_path is None:
            # Default to master UI config in assets
            config_path = Path(__file__).parent.parent.parent.parent / "assets" / "data" / "ui" / "master_ui_config.json"
        
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._color_cache: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> bool:
        """Load UI configuration from file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            print(f"✅ Loaded UI config from {self.config_path}")
            self._clear_color_cache()
            return True
            
        except FileNotFoundError:
            print(f"❌ UI config file not found: {self.config_path}")
            self.config = self._get_fallback_config()
            return False
            
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in UI config: {e}")
            self.config = self._get_fallback_config()
            return False
    
    def reload_config(self) -> bool:
        """Reload configuration from file (useful for hot-reloading during development)."""
        return self.load_config()
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation path.
        
        Args:
            path: Dot-separated path like 'panels.control_panel.position.x'
            default: Default value if path not found
            
        Returns:
            Configuration value or default
        """
        try:
            value = self.config
            for key in path.split('.'):
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_position(self, path: str, default: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """
        Get position configuration.
        
        Args:
            path: Path to position config (e.g., 'panels.control_panel.position')
            default: Default position dict
            
        Returns:
            Position dict with x, y, z keys
        """
        pos = self.get(path, default or {"x": 0.0, "y": 0.0, "z": 0.0})
        
        # Ensure all required keys exist
        return {
            "x": pos.get("x", 0.0),
            "y": pos.get("y", 0.0), 
            "z": pos.get("z", 0.0)
        }
    
    def get_position_tuple(self, path: str, default: Optional[Tuple[float, float, float]] = None) -> Tuple[float, float, float]:
        """
        Get position as tuple for Ursina compatibility.
        
        Args:
            path: Path to position config
            default: Default position tuple
            
        Returns:
            Position tuple (x, y, z)
        """
        pos = self.get_position(path)
        return (pos["x"], pos["y"], pos["z"])
    
    def get_scale(self, path: str, default: Union[float, Dict[str, float]] = 1.0) -> Union[float, Dict[str, float]]:
        """
        Get scale configuration.
        
        Args:
            path: Path to scale config
            default: Default scale value
            
        Returns:
            Scale value (float) or scale dict with x, y, z keys
        """
        scale = self.get(path, default)
        
        # Handle both single values and dict formats
        if isinstance(scale, dict):
            return {
                "x": scale.get("x", 1.0),
                "y": scale.get("y", 1.0),
                "z": scale.get("z", 1.0)
            }
        else:
            return float(scale)
    
    def get_color(self, path: str, default: str = "#FFFFFF") -> Any:
        """
        Get color configuration and convert to Ursina color if available.
        
        Args:
            path: Path to color config
            default: Default color hex string
            
        Returns:
            Ursina color object if available, otherwise hex string
        """
        # Check cache first
        cache_key = f"{path}:{default}"
        if cache_key in self._color_cache:
            return self._color_cache[cache_key]
        
        color_hex = self.get(path, default)
        
        if URSINA_AVAILABLE:
            ursina_color = self._hex_to_ursina_color(color_hex)
            self._color_cache[cache_key] = ursina_color
            return ursina_color
        else:
            self._color_cache[cache_key] = color_hex
            return color_hex
    
    def get_action_color(self, action_type: str) -> Any:
        """
        Get color for specific action type.
        
        Args:
            action_type: Action type like 'Attack', 'Magic', etc.
            
        Returns:
            Ursina color object or hex string
        """
        return self.get_color(f"colors.action_types.{action_type}", "#FFFFFF")
    
    def get_ui_state_color(self, state: str) -> Any:
        """
        Get color for UI state like 'normal', 'hover', 'selected', etc.
        
        Args:
            state: UI state name
            
        Returns:
            Ursina color object or hex string
        """
        return self.get_color(f"colors.ui_states.{state}", "#FFFFFF")
    
    def get_tile_highlight_color(self, highlight_type: str) -> Any:
        """
        Get color for tile highlighting.
        
        Args:
            highlight_type: Type like 'selected', 'movement_range', etc.
            
        Returns:
            Ursina color object or hex string
        """
        return self.get_color(f"colors.tile_highlights.{highlight_type}", "#FFFFFF")
    
    def get_text_config(self, path: str) -> Dict[str, Any]:
        """
        Get text configuration including color, scale, and position.
        
        Args:
            path: Path to text config
            
        Returns:
            Dict with text properties
        """
        config = self.get(path, {})
        
        return {
            "text": config.get("text", ""),
            "position": self.get_position_tuple(f"{path}.position"),
            "scale": config.get("scale", 1.0),
            "color": self.get_color(f"{path}.color", "#FFFFFF"),
            "origin": config.get("origin", {"x": 0.0, "y": 0.0})
        }
    
    def get_modal_config(self, modal_name: str) -> Dict[str, Any]:
        """
        Get complete modal configuration.
        
        Args:
            modal_name: Name of modal like 'movement_confirmation'
            
        Returns:
            Complete modal configuration dict
        """
        modal_config = self.get(f"modals.{modal_name}", {})
        common_config = self.get("modals.common_settings", {})
        
        # Merge common settings with specific modal settings
        config = {**common_config, **modal_config}
        
        # Convert colors
        if "background_color" in config:
            config["background_color"] = self.get_color(f"modals.{modal_name}.background_color", 
                                                       common_config.get("background_color", "#1A1A26"))
        
        return config
    
    def get_animation_config(self, animation_type: str) -> Dict[str, Any]:
        """
        Get animation configuration.
        
        Args:
            animation_type: Type like 'fade', 'scale', etc.
            
        Returns:
            Animation configuration dict
        """
        return self.get(f"animations.{animation_type}", {})
    
    def _hex_to_ursina_color(self, hex_color: str) -> Any:
        """Convert hex color string to Ursina color object."""
        if not URSINA_AVAILABLE:
            return hex_color
        
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        
        # Handle different hex formats
        if len(hex_color) == 6:
            # RGB format
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            return color.rgb(r, g, b)
        elif len(hex_color) == 8:
            # RGBA format
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            a = int(hex_color[6:8], 16) / 255.0
            return color.rgba(r, g, b, a)
        else:
            # Fallback to white
            return color.white
    
    def _clear_color_cache(self):
        """Clear the color conversion cache."""
        self._color_cache.clear()
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """Get minimal fallback configuration if main config fails to load."""
        return {
            "version": "2.0.0",
            "colors": {
                "action_types": {
                    "Attack": "#FF0000",
                    "Magic": "#0000FF", 
                    "Spirit": "#FFFF00",
                    "Move": "#00FF00",
                    "Default": "#FFFFFF"
                },
                "ui_states": {
                    "normal": "#FFFFFF",
                    "selected": "#FFFF00",
                    "disabled": "#666666"
                }
            },
            "hotkey_system": {
                "slot_layout": {
                    "start_position": {"x": -0.4, "y": 0.35, "z": 0.0},
                    "slot_size": 0.06,
                    "slot_spacing": 0.01
                }
            }
        }
    
    def validate_config(self) -> Dict[str, list]:
        """
        Validate the loaded configuration for common issues.
        
        Returns:
            Dict with validation results (errors, warnings)
        """
        errors = []
        warnings = []
        
        # Check required sections
        required_sections = ["colors", "panels", "ui_bars", "hotkey_system"]
        for section in required_sections:
            if section not in self.config:
                errors.append(f"Missing required section: {section}")
        
        # Check coordinate ranges
        def check_coordinate(path: str, coord: str, min_val: float = -1.0, max_val: float = 1.0):
            value = self.get(f"{path}.{coord}")
            if value is not None and not (min_val <= value <= max_val):
                warnings.append(f"Coordinate {path}.{coord} = {value} is outside normal range [{min_val}, {max_val}]")
        
        # Check some common position coordinates
        position_paths = [
            "panels.control_panel.main_panel.position",
            "ui_bars.health_bar.position", 
            "hotkey_system.slot_layout.start_position"
        ]
        
        for path in position_paths:
            check_coordinate(path, "x")
            check_coordinate(path, "y")
        
        return {"errors": errors, "warnings": warnings}
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information about the config manager."""
        return {
            "config_path": str(self.config_path),
            "config_loaded": bool(self.config),
            "version": self.get("version", "unknown"),
            "color_cache_size": len(self._color_cache),
            "ursina_available": URSINA_AVAILABLE
        }


# Global instance for easy access
_ui_config_manager: Optional[UIConfigManager] = None


def get_ui_config_manager() -> UIConfigManager:
    """Get the global UI config manager instance."""
    global _ui_config_manager
    if _ui_config_manager is None:
        _ui_config_manager = UIConfigManager()
    return _ui_config_manager


def reload_ui_config():
    """Reload the UI configuration (useful for development)."""
    global _ui_config_manager
    if _ui_config_manager is not None:
        _ui_config_manager.reload_config()


# Convenience functions for common operations
def get_ui_color(path: str, default: str = "#FFFFFF") -> Any:
    """Get UI color using global config manager."""
    return get_ui_config_manager().get_color(path, default)


def get_ui_position(path: str, default: Optional[Tuple[float, float, float]] = None) -> Tuple[float, float, float]:
    """Get UI position tuple using global config manager."""
    return get_ui_config_manager().get_position_tuple(path, default)


def get_ui_scale(path: str, default: float = 1.0) -> Union[float, Dict[str, float]]:
    """Get UI scale using global config manager."""
    return get_ui_config_manager().get_scale(path, default)


def get_action_color(action_type: str) -> Any:
    """Get color for action type using global config manager."""
    return get_ui_config_manager().get_action_color(action_type)