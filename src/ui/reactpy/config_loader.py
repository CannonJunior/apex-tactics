"""
ReactPy UI Config Loader

Loads UI configuration from master_ui_config.json for ReactPy components.
Provides the same configuration system as the Ursina UI.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


class ReactPyConfigLoader:
    """Loads and provides UI configuration for ReactPy components"""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self):
        """Load master UI configuration"""
        try:
            # Get path to master UI config
            current_dir = Path(__file__).parent
            config_path = current_dir.parent.parent.parent.parent / "assets" / "data" / "ui" / "master_ui_config.json"
            
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                print(f"✅ ReactPy: Loaded UI config from {config_path}")
            else:
                print(f"⚠️ ReactPy: Config file not found: {config_path}")
                self._load_fallback_config()
                
        except Exception as e:
            print(f"❌ ReactPy: Error loading UI config: {e}")
            self._load_fallback_config()
    
    def _load_fallback_config(self):
        """Load fallback configuration if file loading fails"""
        self.config = {
            "panels": {
                "control_panel": {
                    "end_turn_button": {
                        "position": {"x": -0.7, "y": 0.3, "z": 0.01},
                        "scale": 0.08,
                        "color": "#FFA500",
                        "text": "End Turn",
                        "text_color": "#000000",
                        "text_scale": 1.0
                    }
                }
            }
        }
        print("📦 ReactPy: Using fallback UI config")
    
    def get(self, path: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated path"""
        try:
            keys = path.split('.')
            current = self.config
            
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default
            
            return current
        except Exception:
            return default
    
    def get_color(self, path: str, default_color: str = "#FFFFFF") -> str:
        """Get color value as hex string"""
        color_value = self.get(path, default_color)
        
        # Ensure it's a valid hex color
        if isinstance(color_value, str) and color_value.startswith('#'):
            return color_value
        else:
            return default_color
    
    def get_position(self, path: str, default: Dict[str, float] = None) -> Dict[str, float]:
        """Get position as dictionary with x, y, z keys"""
        if default is None:
            default = {"x": 0.0, "y": 0.0, "z": 0.0}
        
        pos_data = self.get(path, default)
        
        if isinstance(pos_data, dict):
            return {
                "x": pos_data.get("x", default["x"]),
                "y": pos_data.get("y", default["y"]),
                "z": pos_data.get("z", default["z"])
            }
        else:
            return default
    
    def get_css_position(self, path: str, viewport_width: int = 1920, viewport_height: int = 1080) -> Dict[str, str]:
        """Convert normalized position to CSS position"""
        pos = self.get_position(path)
        
        # Convert normalized coordinates (-1 to 1) to CSS pixels
        # Ursina: x=0 is center, y=0 is center
        # CSS: left=0 is left edge, top=0 is top edge
        
        css_left = (pos["x"] + 1.0) * viewport_width / 2.0
        css_top = (1.0 - pos["y"]) * viewport_height / 2.0  # Flip Y axis
        
        return {
            "left": f"{css_left}px",
            "top": f"{css_top}px",
            "z-index": str(int(pos["z"] * 1000 + 1000))  # Convert z to CSS z-index
        }
    
    def get_css_scale(self, path: str, base_size: int = 100) -> Dict[str, str]:
        """Convert normalized scale to CSS size"""
        scale = self.get(path, 1.0)
        
        if isinstance(scale, (int, float)):
            size = int(scale * base_size)
            return {
                "width": f"{size}px",
                "height": f"{size}px"
            }
        else:
            return {
                "width": f"{base_size}px",
                "height": f"{base_size}px"
            }


# Global instance
_config_loader: Optional[ReactPyConfigLoader] = None


def get_reactpy_config() -> ReactPyConfigLoader:
    """Get the global ReactPy config loader instance"""
    global _config_loader
    
    if _config_loader is None:
        _config_loader = ReactPyConfigLoader()
    
    return _config_loader