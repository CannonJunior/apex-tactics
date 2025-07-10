"""
Talent Tree Manager

Manages loading and access to talent tree data from asset files.
Provides centralized talent tree management for the game.
"""

import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path


class TalentManager:
    """
    Manages talent trees and abilities loaded from asset files.
    
    Features:
    - Load talent trees from JSON files
    - Provide access to talent data by tree type
    - Validate talent prerequisites
    - Track learned talents per character
    """
    
    def __init__(self, assets_path: Optional[str] = None):
        """
        Initialize talent manager.
        
        Args:
            assets_path: Path to assets directory (optional)
        """
        if assets_path is None:
            # Default to assets directory relative to this file
            current_dir = Path(__file__).parent
            self.assets_path = current_dir.parent.parent.parent / "assets" / "data" / "abilities"
        else:
            self.assets_path = Path(assets_path)
        
        self.talent_trees: Dict[str, Dict[str, Any]] = {}
        self.talent_lookup: Dict[str, Dict[str, Any]] = {}  # talent_id -> talent data
        self._load_talent_trees()
    
    def _load_talent_trees(self):
        """Load all talent trees from asset files."""
        try:
            # Load physical talents
            physical_file = self.assets_path / "physical_talents.json"
            if physical_file.exists():
                with open(physical_file, 'r', encoding='utf-8') as f:
                    physical_data = json.load(f)
                    self.talent_trees["Physical"] = physical_data
                    self._index_talents("Physical", physical_data["talents"])
                    print(f"✅ Loaded {len(physical_data['talents'])} physical talents")
            
            # Load magical talents
            magical_file = self.assets_path / "magical_talents.json"
            if magical_file.exists():
                with open(magical_file, 'r', encoding='utf-8') as f:
                    magical_data = json.load(f)
                    self.talent_trees["Magical"] = magical_data
                    self._index_talents("Magical", magical_data["talents"])
                    print(f"✅ Loaded {len(magical_data['talents'])} magical talents")
            
            # Load spiritual talents
            spiritual_file = self.assets_path / "spiritual_talents.json"
            if spiritual_file.exists():
                with open(spiritual_file, 'r', encoding='utf-8') as f:
                    spiritual_data = json.load(f)
                    self.talent_trees["Spiritual"] = spiritual_data
                    self._index_talents("Spiritual", spiritual_data["talents"])
                    print(f"✅ Loaded {len(spiritual_data['talents'])} spiritual talents")
            
            if not self.talent_trees:
                print("⚠️ No talent trees loaded, using fallback data")
                self._load_fallback_talents()
                
        except Exception as e:
            print(f"❌ Error loading talent trees: {e}")
            self._load_fallback_talents()
    
    def _index_talents(self, tree_name: str, talents: List[Dict[str, Any]]):
        """Index talents for quick lookup by ID."""
        for talent in talents:
            talent_id = talent.get('id')
            if talent_id:
                self.talent_lookup[talent_id] = {
                    **talent,
                    'tree': tree_name
                }
    
    def _load_fallback_talents(self):
        """Load fallback talent data if asset files are not available."""
        self.talent_trees = {
            "Physical": {
                "talent_tree_name": "Physical",
                "description": "Physical combat abilities",
                "talents": [
                    {"id": "basic_strike", "name": "Basic Strike", "level": 1, "tier": "Novice", "description": "Basic melee attack"},
                    {"id": "power_attack", "name": "Power Attack", "level": 2, "tier": "Novice", "description": "Stronger but slower attack"},
                    {"id": "weapon_mastery", "name": "Weapon Mastery", "level": 3, "tier": "Adept", "description": "Increased weapon proficiency"},
                ]
            },
            "Magical": {
                "talent_tree_name": "Magical",
                "description": "Arcane spells and abilities",
                "talents": [
                    {"id": "magic_missile", "name": "Magic Missile", "level": 1, "tier": "Novice", "description": "Basic ranged spell"},
                    {"id": "heal", "name": "Heal", "level": 2, "tier": "Novice", "description": "Restore health points"},
                    {"id": "fireball", "name": "Fireball", "level": 3, "tier": "Adept", "description": "Area damage spell"},
                ]
            },
            "Spiritual": {
                "talent_tree_name": "Spiritual",
                "description": "Spiritual abilities",
                "talents": [
                    {"id": "inner_peace", "name": "Inner Peace", "level": 1, "tier": "Novice", "description": "Restore mental energy"},
                    {"id": "blessing", "name": "Blessing", "level": 2, "tier": "Novice", "description": "Temporary stat boost"},
                    {"id": "spirit_shield", "name": "Spirit Shield", "level": 3, "tier": "Adept", "description": "Magical damage protection"},
                ]
            }
        }
        
        # Re-index fallback talents
        for tree_name, tree_data in self.talent_trees.items():
            self._index_talents(tree_name, tree_data["talents"])
    
    def get_talent_tree(self, tree_name: str) -> Optional[Dict[str, Any]]:
        """
        Get talent tree data by name.
        
        Args:
            tree_name: Name of talent tree (Physical, Magical, Spiritual)
            
        Returns:
            Talent tree data or None if not found
        """
        return self.talent_trees.get(tree_name)
    
    def get_talents_for_ui(self, tree_name: str) -> List[Dict[str, Any]]:
        """
        Get talent list formatted for UI display.
        
        Args:
            tree_name: Name of talent tree
            
        Returns:
            List of talents with UI-friendly format
        """
        tree_data = self.get_talent_tree(tree_name)
        if not tree_data:
            return []
        
        talents = tree_data.get("talents", [])
        ui_talents = []
        
        for talent in talents:
            ui_talent = {
                "name": talent.get("name", "Unknown"),
                "level": talent.get("level", 1),
                "tier": talent.get("tier", "Novice"),
                "description": talent.get("description", "No description"),
                "learned": False,  # Default to not learned
                "id": talent.get("id", "")
            }
            ui_talents.append(ui_talent)
        
        return ui_talents
    
    def get_talent_by_id(self, talent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get talent data by ID.
        
        Args:
            talent_id: Unique talent identifier
            
        Returns:
            Talent data or None if not found
        """
        return self.talent_lookup.get(talent_id)
    
    def get_all_talents(self) -> List[Dict[str, Any]]:
        """
        Get all talents from all trees.
        
        Returns:
            List of all talent data dictionaries
        """
        return list(self.talent_lookup.values())
    
    def get_available_trees(self) -> List[str]:
        """
        Get list of available talent tree names.
        
        Returns:
            List of talent tree names
        """
        return list(self.talent_trees.keys())
    
    def validate_prerequisites(self, talent_id: str, learned_talents: List[str]) -> bool:
        """
        Check if talent prerequisites are met.
        
        Args:
            talent_id: ID of talent to check
            learned_talents: List of already learned talent IDs
            
        Returns:
            True if prerequisites are met
        """
        talent = self.get_talent_by_id(talent_id)
        if not talent:
            return False
        
        requirements = talent.get("requirements", {})
        prerequisites = requirements.get("prerequisites", [])
        
        # Check if all prerequisites are learned
        for prereq_id in prerequisites:
            if prereq_id not in learned_talents:
                return False
        
        return True
    
    def get_talent_cost(self, talent_id: str) -> Dict[str, Any]:
        """
        Get the cost to learn a talent.
        
        Args:
            talent_id: ID of talent
            
        Returns:
            Dictionary with cost information
        """
        talent = self.get_talent_by_id(talent_id)
        if not talent:
            return {}
        
        return talent.get("cost", {})
    
    def get_talent_effects(self, talent_id: str) -> Dict[str, Any]:
        """
        Get the effects of a talent.
        
        Args:
            talent_id: ID of talent
            
        Returns:
            Dictionary with effect information
        """
        talent = self.get_talent_by_id(talent_id)
        if not talent:
            return {}
        
        return talent.get("effects", {})


# Global talent manager instance
_talent_manager = None

def get_talent_manager() -> TalentManager:
    """
    Get global talent manager instance.
    
    Returns:
        TalentManager instance
    """
    global _talent_manager
    if _talent_manager is None:
        _talent_manager = TalentManager()
    return _talent_manager