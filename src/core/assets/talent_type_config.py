"""
Talent Type Configuration Manager

Loads and manages talent type configurations including highlighting colors,
targeting behaviors, and resource costs.
"""

import json
import os
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

try:
    from ursina import color
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False


class TalentTypeConfig:
    """
    Manages talent type configurations and provides access to talent type properties.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize talent type configuration.
        
        Args:
            config_path: Path to talent types config file. If None, auto-detects.
        """
        self._config_data: Dict[str, Any] = {}
        
        # Auto-detect config path if not provided
        if config_path is None:
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent
            self.config_path = project_root / "assets" / "data" / "config" / "talent_types.json"
        else:
            self.config_path = Path(config_path)
        
        self._load_config()
    
    def _load_config(self):
        """Load talent type configuration from JSON file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self._config_data = json.load(f)
                print(f"Loaded talent type config from {self.config_path}")
            else:
                print(f"Warning: Talent type config not found at {self.config_path}, using defaults")
                self._load_default_config()
        except Exception as e:
            print(f"Error loading talent type config: {e}, using defaults")
            self._load_default_config()
    
    def _load_default_config(self):
        """Load default talent type configuration as fallback."""
        self._config_data = {
            "version": "1.0",
            "talent_types": {
                "Magic": {
                    "highlighting": {
                        "range_color": [0, 0, 1, 1],
                        "range_color_name": "blue",
                        "area_color": [0.5, 0.7, 1.0, 1],
                        "target_color": [0, 0, 1, 1]
                    },
                    "targeting": {"requires_targeting": True},
                    "default_range": 3
                },
                "Attack": {
                    "highlighting": {
                        "range_color": [1, 0, 0, 1],
                        "range_color_name": "red",
                        "area_color": [1, 0.5, 0.5, 1],
                        "target_color": [1, 0, 0, 1]
                    },
                    "targeting": {"requires_targeting": True},
                    "default_range": 1
                },
                "Spirit": {
                    "highlighting": {
                        "range_color": [1, 1, 0, 1],
                        "range_color_name": "yellow",
                        "area_color": [1, 1, 0.5, 1],
                        "target_color": [1, 1, 0, 1]
                    },
                    "targeting": {"requires_targeting": True},
                    "default_range": 2
                }
            }
        }
    
    def get_talent_type_config(self, talent_type: str) -> Dict[str, Any]:
        """
        Get complete configuration for a talent type.
        
        Args:
            talent_type: Name of the talent type (e.g., "Magic", "Attack", "Spirit")
            
        Returns:
            Dictionary containing all configuration for the talent type
        """
        talent_types = self._config_data.get('talent_types', {})
        return talent_types.get(talent_type, talent_types.get('Magic', {}))
    
    def get_highlighting_config(self, talent_type: str) -> Dict[str, Any]:
        """
        Get highlighting configuration for a talent type.
        
        Args:
            talent_type: Name of the talent type
            
        Returns:
            Dictionary containing highlighting properties
        """
        config = self.get_talent_type_config(talent_type)
        return config.get('highlighting', {})
    
    def get_range_color(self, talent_type: str):
        """
        Get the range highlighting color for a talent type.
        
        Args:
            talent_type: Name of the talent type
            
        Returns:
            Ursina color object or RGB tuple
        """
        highlighting = self.get_highlighting_config(talent_type)
        
        if URSINA_AVAILABLE:
            # Try to get color by name first
            color_name = highlighting.get('range_color_name', 'blue')
            if hasattr(color, color_name):
                return getattr(color, color_name)
            
            # Fall back to RGBA values
            rgba = highlighting.get('range_color', [0, 0, 1, 1])
            return color.Color(*rgba)
        else:
            # Return RGB tuple if Ursina not available
            return highlighting.get('range_color', [0, 0, 1])
    
    def get_area_color(self, talent_type: str):
        """
        Get the area highlighting color for a talent type.
        
        Args:
            talent_type: Name of the talent type
            
        Returns:
            Ursina color object or RGB tuple
        """
        highlighting = self.get_highlighting_config(talent_type)
        
        if URSINA_AVAILABLE:
            # Try to get color by name first
            color_name = highlighting.get('area_color_name', 'light_blue')
            if hasattr(color, color_name):
                return getattr(color, color_name)
            
            # Fall back to RGBA values
            rgba = highlighting.get('area_color', [0.5, 0.7, 1.0, 1])
            return color.Color(*rgba)
        else:
            # Return RGB tuple if Ursina not available
            return highlighting.get('area_color', [0.5, 0.7, 1.0])
    
    def get_target_color(self, talent_type: str):
        """
        Get the target highlighting color for a talent type.
        
        Args:
            talent_type: Name of the talent type
            
        Returns:
            Ursina color object or RGB tuple
        """
        highlighting = self.get_highlighting_config(talent_type)
        
        if URSINA_AVAILABLE:
            # Try to get color by name first
            color_name = highlighting.get('target_color_name', 'blue')
            if hasattr(color, color_name):
                return getattr(color, color_name)
            
            # Fall back to RGBA values
            rgba = highlighting.get('target_color', [0, 0, 1, 1])
            return color.Color(*rgba)
        else:
            # Return RGB tuple if Ursina not available
            return highlighting.get('target_color', [0, 0, 1])
    
    def get_targeting_config(self, talent_type: str) -> Dict[str, Any]:
        """
        Get targeting configuration for a talent type.
        
        Args:
            talent_type: Name of the talent type
            
        Returns:
            Dictionary containing targeting behavior properties
        """
        config = self.get_talent_type_config(talent_type)
        return config.get('targeting', {})
    
    def requires_targeting(self, talent_type: str) -> bool:
        """
        Check if a talent type requires target selection.
        
        Args:
            talent_type: Name of the talent type
            
        Returns:
            True if targeting is required, False otherwise
        """
        targeting = self.get_targeting_config(talent_type)
        return targeting.get('requires_targeting', True)
    
    def show_area_preview(self, talent_type: str) -> bool:
        """
        Check if a talent type should show area preview highlighting.
        
        Args:
            talent_type: Name of the talent type
            
        Returns:
            True if area preview should be shown, False otherwise
        """
        targeting = self.get_targeting_config(talent_type)
        return targeting.get('show_area_preview', True)
    
    def show_confirmation_modal(self, talent_type: str) -> bool:
        """
        Check if a talent type should show confirmation modal.
        
        Args:
            talent_type: Name of the talent type
            
        Returns:
            True if confirmation modal should be shown, False otherwise
        """
        targeting = self.get_targeting_config(talent_type)
        return targeting.get('confirmation_modal', True)
    
    def get_default_range(self, talent_type: str) -> int:
        """
        Get the default range for a talent type.
        
        Args:
            talent_type: Name of the talent type
            
        Returns:
            Default range value
        """
        config = self.get_talent_type_config(talent_type)
        return config.get('default_range', 3)
    
    def get_default_area(self, talent_type: str) -> int:
        """
        Get the default area of effect for a talent type.
        
        Args:
            talent_type: Name of the talent type
            
        Returns:
            Default area of effect value
        """
        config = self.get_talent_type_config(talent_type)
        return config.get('default_area', 1)
    
    def get_resource_costs(self, talent_type: str) -> list:
        """
        Get the possible resource cost types for a talent type.
        
        Args:
            talent_type: Name of the talent type
            
        Returns:
            List of resource cost types (e.g., ["mp_cost", "kwan_cost"])
        """
        config = self.get_talent_type_config(talent_type)
        return config.get('resource_costs', ['mp_cost'])
    
    def reload_config(self):
        """Reload configuration from file."""
        self._load_config()


# Global instance for easy access
_talent_type_config = None

def get_talent_type_config() -> TalentTypeConfig:
    """
    Get the global talent type configuration instance.
    
    Returns:
        TalentTypeConfig instance
    """
    global _talent_type_config
    if _talent_type_config is None:
        _talent_type_config = TalentTypeConfig()
    return _talent_type_config