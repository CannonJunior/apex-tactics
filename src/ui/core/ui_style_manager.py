"""
UI Style Manager

Loads and manages UI styling configuration from assets/ui_styles.json.
Provides color conversion and style access methods for UI components.
"""

import json
import os
from typing import Dict, Any, Optional, Tuple

try:
    from ursina import color
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False


class UIStyleManager:
    """
    Manages UI styling configuration and provides color conversion utilities.
    """
    
    def __init__(self, styles_file_path: str = None):
        """
        Initialize UI Style Manager.
        
        Args:
            styles_file_path: Optional path to styles file, defaults to assets/ui_styles.json
        """
        self.styles: Dict[str, Any] = {}
        self.loaded = False
        
        # Default to assets/ui_styles.json if no path provided
        if styles_file_path is None:
            # Get the project root directory (assuming this file is in src/ui/core/)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(current_dir, "..", "..", "..")
            styles_file_path = os.path.join(project_root, "assets", "ui_styles.json")
        
        self.styles_file_path = styles_file_path
        self.load_styles()
    
    def load_styles(self) -> bool:
        """
        Load UI styles from JSON file.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            if os.path.exists(self.styles_file_path):
                with open(self.styles_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.styles = data.get('ui_styles', {})
                    self.loaded = True
                    print(f"✅ UI styles loaded from {self.styles_file_path}")
                    return True
            else:
                print(f"⚠️ UI styles file not found: {self.styles_file_path}")
                self._load_default_styles()
                return False
        except Exception as e:
            print(f"❌ Error loading UI styles: {e}")
            self._load_default_styles()
            return False
    
    def _load_default_styles(self):
        """Load default fallback styles if file loading fails."""
        self.styles = {
            "bars": {
                "health_bar": {
                    "color": {"r": 0.0, "g": 0.8, "b": 0.0, "a": 1.0},
                    "background_color": {"r": 0.2, "g": 0.2, "b": 0.2, "a": 1.0}
                },
                "resource_bars": {
                    "rage": {"color": {"r": 1.0, "g": 0.0, "b": 0.0, "a": 1.0}, "label": "RAGE"},
                    "mp": {"color": {"r": 0.0, "g": 0.0, "b": 1.0, "a": 1.0}, "label": "MP"},
                    "kwan": {"color": {"r": 1.0, "g": 1.0, "b": 0.0, "a": 1.0}, "label": "KWAN"}
                }
            },
            "inventory": {
                "item_type_colors": {
                    "Weapons": {"r": 0.8, "g": 0.2, "b": 0.2, "a": 1.0},
                    "Armor": {"r": 0.2, "g": 0.6, "b": 0.8, "a": 1.0},
                    "Accessories": {"r": 0.9, "g": 0.7, "b": 0.2, "a": 1.0},
                    "Consumables": {"r": 0.2, "g": 0.8, "b": 0.2, "a": 1.0},
                    "Materials": {"r": 0.6, "g": 0.4, "b": 0.8, "a": 1.0}
                },
                "equipped_highlight": {
                    "border_color": {"r": 1.0, "g": 1.0, "b": 0.0, "a": 1.0},
                    "border_width": 0.02
                }
            }
        }
        self.loaded = True
        print("📦 Using default UI styles")
    
    def get_style(self, style_path: str, default: Any = None) -> Any:
        """
        Get a style value by dot-separated path.
        
        Args:
            style_path: Dot-separated path like 'bars.health_bar.color'
            default: Default value if path not found
            
        Returns:
            Style value or default
        """
        try:
            keys = style_path.split('.')
            current = self.styles
            
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default
            
            return current
        except Exception:
            return default
    
    def get_color(self, style_path: str, default_color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)) -> Any:
        """
        Get a color from styles and convert to Ursina color if available.
        
        Args:
            style_path: Path to color config like 'bars.health_bar.color'
            default_color: Default RGBA tuple if color not found
            
        Returns:
            Ursina color object if available, otherwise color dict
        """
        color_config = self.get_style(style_path)
        
        if color_config and isinstance(color_config, dict):
            r = color_config.get('r', default_color[0])
            g = color_config.get('g', default_color[1])
            b = color_config.get('b', default_color[2])
            a = color_config.get('a', default_color[3])
        else:
            r, g, b, a = default_color
        
        # Convert to Ursina color if available
        if URSINA_AVAILABLE:
            return color.Color(r, g, b, a)
        else:
            return {'r': r, 'g': g, 'b': b, 'a': a}
    
    def get_health_bar_color(self) -> Any:
        """Get health bar color from styles."""
        return self.get_color('bars.health_bar.color', (0.0, 0.8, 0.0, 1.0))
    
    def get_health_bar_bg_color(self) -> Any:
        """Get health bar background color from styles."""
        return self.get_color('bars.health_bar.background_color', (0.2, 0.2, 0.2, 1.0))
    
    def get_resource_bar_color(self, resource_type: str) -> Any:
        """
        Get resource bar color based on resource type.
        
        Args:
            resource_type: 'rage', 'mp', or 'kwan'
            
        Returns:
            Ursina color for the resource type
        """
        color_path = f'bars.resource_bars.{resource_type}.color'
        
        # Default colors for each resource type
        defaults = {
            'rage': (1.0, 0.0, 0.0, 1.0),    # Red
            'mp': (0.0, 0.0, 1.0, 1.0),      # Blue
            'kwan': (1.0, 1.0, 0.0, 1.0)     # Yellow
        }
        
        default_color = defaults.get(resource_type, (0.5, 0.5, 0.5, 1.0))
        return self.get_color(color_path, default_color)
    
    def get_resource_bar_bg_color(self) -> Any:
        """Get resource bar background color from styles."""
        return self.get_color('bars.resource_bars.background_color', (0.2, 0.2, 0.2, 1.0))
    
    def get_resource_bar_label(self, resource_type: str) -> str:
        """
        Get resource bar label text.
        
        Args:
            resource_type: 'rage', 'mp', or 'kwan'
            
        Returns:
            Label text for the resource type
        """
        label_path = f'bars.resource_bars.{resource_type}.label'
        
        # Default labels
        defaults = {
            'rage': 'RAGE',
            'mp': 'MP',
            'kwan': 'KWAN'
        }
        
        return self.get_style(label_path, defaults.get(resource_type, resource_type.upper()))
    
    def get_bar_label_color(self) -> Any:
        """Get bar label text color from styles."""
        return self.get_color('labels.bar_labels.color', (1.0, 1.0, 1.0, 1.0))
    
    def get_highlight_color(self, highlight_type: str) -> Any:
        """
        Get highlight color by type.
        
        Args:
            highlight_type: 'movement', 'attack', 'selection', 'effect_area'
            
        Returns:
            Ursina color for the highlight type
        """
        color_path = f'highlights.{highlight_type}.color'
        return self.get_color(color_path, (1.0, 1.0, 1.0, 0.5))
    
    def get_item_type_color(self, item_type: str) -> Any:
        """
        Get color for a specific item type.
        
        Args:
            item_type: 'Weapons', 'Armor', 'Accessories', 'Consumables', 'Materials'
            
        Returns:
            Ursina color for the item type
        """
        color_path = f'inventory.item_type_colors.{item_type}'
        
        # Default colors for each item type
        defaults = {
            'Weapons': (0.8, 0.2, 0.2, 1.0),      # Red
            'Armor': (0.2, 0.6, 0.8, 1.0),        # Blue
            'Accessories': (0.9, 0.7, 0.2, 1.0),  # Gold
            'Consumables': (0.2, 0.8, 0.2, 1.0),  # Green
            'Materials': (0.6, 0.4, 0.8, 1.0)     # Purple
        }
        
        default_color = defaults.get(item_type, (1.0, 1.0, 1.0, 1.0))
        return self.get_color(color_path, default_color)
    
    def get_equipped_highlight_color(self) -> Any:
        """Get equipped item highlight border color from styles."""
        return self.get_color('inventory.equipped_highlight.border_color', (1.0, 1.0, 0.0, 1.0))
    
    def get_equipped_highlight_width(self) -> float:
        """Get equipped item highlight border width from styles."""
        return self.get_style('inventory.equipped_highlight.border_width', 0.02)
    
    def reload_styles(self) -> bool:
        """
        Reload styles from file.
        
        Returns:
            True if reloaded successfully
        """
        return self.load_styles()


# Global instance for easy access
_style_manager_instance: Optional[UIStyleManager] = None


def get_ui_style_manager() -> UIStyleManager:
    """
    Get the global UI style manager instance.
    
    Returns:
        UIStyleManager singleton instance
    """
    global _style_manager_instance
    
    if _style_manager_instance is None:
        _style_manager_instance = UIStyleManager()
    
    return _style_manager_instance


def reload_ui_styles() -> bool:
    """
    Reload UI styles from file.
    
    Returns:
        True if reloaded successfully
    """
    style_manager = get_ui_style_manager()
    return style_manager.reload_styles()