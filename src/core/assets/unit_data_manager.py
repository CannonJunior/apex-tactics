"""
Unit Data Manager

Centralized loading and management of unit parameters from asset files.
Provides a single interface for accessing unit colors, stats, AI parameters, etc.
"""

import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

try:
    from ursina import color
    URSINA_AVAILABLE = True
except ImportError:
    URSINA_AVAILABLE = False

from core.models.unit_types import UnitType


class UnitDataManager:
    """
    Centralized manager for unit configuration data.
    
    Loads unit parameters from JSON files and provides a unified interface
    for accessing unit colors, stats, AI parameters, and other configuration.
    """
    
    def __init__(self, assets_path: Optional[str] = None):
        """
        Initialize the unit data manager.
        
        Args:
            assets_path: Path to assets directory. If None, auto-detects from project structure.
        """
        self._character_types_data: Dict[str, Any] = {}
        self._unit_types_data: Dict[str, Any] = {}
        self._generation_data: Dict[str, Any] = {}
        self._ai_difficulty_data: Dict[str, Any] = {}
        
        # Auto-detect assets path if not provided
        if assets_path is None:
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent
            self.assets_path = project_root / "assets" / "data"
            self.units_path = self.assets_path / "units"
            self.characters_path = self.assets_path / "characters"
        else:
            self.assets_path = Path(assets_path)
            self.units_path = self.assets_path / "units"
            self.characters_path = self.assets_path / "characters"
        
        self._load_all_data()
    
    def _load_all_data(self):
        """Load all unit data from JSON files."""
        try:
            self._load_character_types()
            self._load_unit_types()
            self._load_generation_data()
            self._load_ai_difficulty_data()
        except Exception as e:
            print(f"Warning: Failed to load unit data: {e}")
            # Fall back to hardcoded defaults
            self._load_fallback_data()
    
    def _load_character_types(self):
        """Load character types configuration from multiple files."""
        # Load from all_characters.json first
        all_characters_file = self.characters_path / "all_characters.json"
        if all_characters_file.exists():
            with open(all_characters_file, 'r') as f:
                data = json.load(f)
                self._character_types_data.update(data.get('character_types', {}))
        
        # Load individual character files
        if self.characters_path.exists():
            for char_file in self.characters_path.glob("*_character.json"):
                try:
                    with open(char_file, 'r') as f:
                        data = json.load(f)
                        self._character_types_data.update(data.get('character_types', {}))
                except Exception as e:
                    print(f"Warning: Failed to load character file {char_file}: {e}")
    
    def _load_unit_types(self):
        """Load unit types configuration (fallback)."""
        unit_types_file = self.units_path / "unit_types.json"
        if unit_types_file.exists():
            with open(unit_types_file, 'r') as f:
                data = json.load(f)
                self._unit_types_data = data.get('unit_types', {})
    
    def _load_generation_data(self):
        """Load unit generation configuration."""
        generation_file = self.units_path / "unit_generation.json"
        if generation_file.exists():
            with open(generation_file, 'r') as f:
                data = json.load(f)
                self._generation_data = data.get('unit_generation', {})
    
    def _load_ai_difficulty_data(self):
        """Load AI difficulty configuration."""
        ai_file = self.units_path / "ai_difficulty.json"
        if ai_file.exists():
            with open(ai_file, 'r') as f:
                data = json.load(f)
                self._ai_difficulty_data = data.get('ai_difficulty', {})
    
    def _load_fallback_data(self):
        """Load fallback hardcoded data if files are missing."""
        self._unit_types_data = {
            "heromancer": {"visual": {"color": "orange"}},
            "ubermensch": {"visual": {"color": "red"}},
            "soul_linked": {"visual": {"color": "light_gray"}},
            "realm_walker": {"visual": {"color": [128, 0, 128]}},
            "wargi": {"visual": {"color": "blue"}},
            "magi": {"visual": {"color": "blue"}}
        }
    
    def _get_unit_data(self, unit_type: UnitType) -> Dict[str, Any]:
        """
        Get unit data from character types first, then fallback to unit types.
        
        Args:
            unit_type: UnitType enum value
            
        Returns:
            Dictionary containing unit data
        """
        unit_id = unit_type.value.lower()
        # Try character data first
        if unit_id in self._character_types_data:
            return self._character_types_data[unit_id]
        # Fallback to unit types
        return self._unit_types_data.get(unit_id, {})
    
    def get_unit_color(self, unit_type: UnitType):
        """
        Get the display color for a unit type.
        
        Args:
            unit_type: UnitType enum value
            
        Returns:
            Color object for the unit type
        """
        if not URSINA_AVAILABLE:
            return "white"
        
        unit_data = self._get_unit_data(unit_type)
        visual_data = unit_data.get('visual', {})
        color_value = visual_data.get('color', 'white')
        
        if isinstance(color_value, list) and len(color_value) == 3:
            # RGB tuple - convert to color
            return color.rgb32(*color_value)
        elif isinstance(color_value, str):
            # Color name - get from color module
            return getattr(color, color_value, color.white)
        else:
            return color.white
    
    def get_unit_visual_properties(self, unit_type: UnitType) -> Dict[str, Any]:
        """
        Get all visual properties for a unit type.
        
        Args:
            unit_type: UnitType enum value
            
        Returns:
            Dictionary containing visual properties (color, model, scale)
        """
        unit_data = self._get_unit_data(unit_type)
        visual_data = unit_data.get('visual', {})
        
        return {
            'color': self.get_unit_color(unit_type),
            'model': visual_data.get('model', 'cube'),
            'scale': visual_data.get('scale', [0.8, 2.0, 0.8])
        }
    
    def get_unit_attribute_bonuses(self, unit_type: UnitType) -> List[str]:
        """
        Get attribute bonuses for a unit type.
        
        Args:
            unit_type: UnitType enum value
            
        Returns:
            List of attribute names that get bonuses
        """
        unit_data = self._get_unit_data(unit_type)
        stats_data = unit_data.get('stats', {})
        return stats_data.get('attribute_bonuses', [])
    
    def get_unit_base_stats(self, unit_type: UnitType) -> Dict[str, Any]:
        """
        Get base stats for a unit type.
        
        Args:
            unit_type: UnitType enum value
            
        Returns:
            Dictionary containing base stats
        """
        unit_data = self._get_unit_data(unit_type)
        return unit_data.get('stats', {})
    
    def get_unit_combat_data(self, unit_type: UnitType) -> Dict[str, Any]:
        """
        Get combat data for a unit type.
        
        Args:
            unit_type: UnitType enum value
            
        Returns:
            Dictionary containing combat parameters
        """
        unit_data = self._get_unit_data(unit_type)
        return unit_data.get('combat', {})
    
    def get_unit_ai_data(self, unit_type: UnitType) -> Dict[str, Any]:
        """
        Get AI behavior data for a unit type.
        
        Args:
            unit_type: UnitType enum value
            
        Returns:
            Dictionary containing AI parameters
        """
        unit_data = self._get_unit_data(unit_type)
        return unit_data.get('ai', {})
    
    def get_generation_config(self) -> Dict[str, Any]:
        """
        Get unit generation configuration.
        
        Returns:
            Dictionary containing generation parameters
        """
        return self._generation_data
    
    def get_ai_difficulty_config(self, difficulty: str = 'normal') -> Dict[str, Any]:
        """
        Get AI difficulty configuration.
        
        Args:
            difficulty: Difficulty level ('easy', 'normal', 'hard', 'expert')
            
        Returns:
            Dictionary containing difficulty parameters
        """
        return self._ai_difficulty_data.get(difficulty, self._ai_difficulty_data.get('normal', {}))
    
    def get_all_unit_types(self) -> List[str]:
        """
        Get list of all available unit type IDs.
        
        Returns:
            List of unit type ID strings
        """
        # Combine character types and unit types
        all_types = set(self._character_types_data.keys())
        all_types.update(self._unit_types_data.keys())
        return list(all_types)
    
    def get_unit_display_name(self, unit_type: UnitType) -> str:
        """
        Get display name for a unit type.
        
        Args:
            unit_type: UnitType enum value
            
        Returns:
            Human-readable display name
        """
        unit_data = self._get_unit_data(unit_type)
        return unit_data.get('display_name', unit_type.value.title())
    
    def get_unit_description(self, unit_type: UnitType) -> str:
        """
        Get description for a unit type.
        
        Args:
            unit_type: UnitType enum value
            
        Returns:
            Unit description text
        """
        unit_data = self._get_unit_data(unit_type)
        return unit_data.get('description', '')
    
    def get_unit_inventory(self, unit_type: UnitType) -> Dict[str, Any]:
        """
        Get inventory data for a unit type.
        
        Args:
            unit_type: UnitType enum value
            
        Returns:
            Dictionary containing inventory data (starting_items, max_inventory_size, gold)
        """
        unit_data = self._get_unit_data(unit_type)
        return unit_data.get('inventory', {})
    
    def get_unit_game_state_effects(self, unit_type: UnitType) -> Dict[str, Any]:
        """
        Get game state effects for a unit type.
        
        Args:
            unit_type: UnitType enum value
            
        Returns:
            Dictionary containing game state effects and passive abilities
        """
        unit_data = self._get_unit_data(unit_type)
        return unit_data.get('game_state_effects', {})
    
    def get_unit_talents(self, unit_type: UnitType) -> Dict[str, Any]:
        """
        Get talent tree data for a unit type.
        
        Args:
            unit_type: UnitType enum value
            
        Returns:
            Dictionary containing talent definitions and unlock requirements
        """
        unit_data = self._get_unit_data(unit_type)
        return unit_data.get('talents', {})
    
    def get_unit_hotkey_abilities(self, unit_type: UnitType) -> Dict[str, Any]:
        """
        Get hotkey ability bindings for a unit type.
        
        Args:
            unit_type: UnitType enum value
            
        Returns:
            Dictionary containing hotkey ability mappings (1-9 keys)
        """
        unit_data = self._get_unit_data(unit_type)
        return unit_data.get('hotkey_abilities', {})
    
    def get_starting_items(self, unit_type: UnitType) -> List[Dict[str, Any]]:
        """
        Get starting items for a unit type.
        
        Args:
            unit_type: UnitType enum value
            
        Returns:
            List of starting item dictionaries with item_id, quantity, equipped status
        """
        inventory_data = self.get_unit_inventory(unit_type)
        return inventory_data.get('starting_items', [])
    
    def get_unlocked_talents(self, unit_type: UnitType) -> List[str]:
        """
        Get list of unlocked talent IDs for a unit type.
        
        Args:
            unit_type: UnitType enum value
            
        Returns:
            List of talent IDs that are currently unlocked
        """
        talents_data = self.get_unit_talents(unit_type)
        unlocked = []
        for talent_id, talent_data in talents_data.items():
            if talent_data.get('unlocked', False):
                unlocked.append(talent_id)
        return unlocked
    
    def is_character_type(self, unit_type: UnitType) -> bool:
        """
        Check if a unit type has extended character data.
        
        Args:
            unit_type: UnitType enum value
            
        Returns:
            True if character data exists, False if only basic unit data
        """
        unit_id = unit_type.value.lower()
        return unit_id in self._character_types_data


# Global instance for easy access
_unit_data_manager = None

def get_unit_data_manager() -> UnitDataManager:
    """
    Get the global unit data manager instance.
    
    Returns:
        UnitDataManager instance
    """
    global _unit_data_manager
    if _unit_data_manager is None:
        _unit_data_manager = UnitDataManager()
    return _unit_data_manager