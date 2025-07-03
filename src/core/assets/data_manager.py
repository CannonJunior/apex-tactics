"""
Data Manager

Handles loading and management of game data from asset files.
Provides typed interfaces for different data types like items, abilities, etc.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from .asset_loader import get_asset_loader


@dataclass
class ItemData:
    """Represents an item from the data files."""
    id: str
    name: str
    type: str
    tier: str
    description: str
    stats: Dict[str, Any]
    requirements: Dict[str, Any]
    icon: str
    rarity: str
    value: int
    stackable: bool
    max_stack: int
    enchantments: Optional[List[str]] = None
    consumable: Optional[Dict[str, Any]] = None
    crafting_material: bool = False
    legendary: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ItemData':
        """Create ItemData from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            type=data['type'],
            tier=data['tier'],
            description=data['description'],
            stats=data.get('stats', {}),
            requirements=data.get('requirements', {}),
            icon=data['icon'],
            rarity=data['rarity'],
            value=data['value'],
            stackable=data['stackable'],
            max_stack=data['max_stack'],
            enchantments=data.get('enchantments'),
            consumable=data.get('consumable'),
            crafting_material=data.get('crafting_material', False),
            legendary=data.get('legendary', False)
        )
    
    def to_inventory_format(self, equipped_by: str = None, quantity: int = 1) -> Dict[str, Any]:
        """Convert to inventory panel format."""
        return {
            "name": self.name,
            "type": self.type,
            "tier": self.tier,
            "equipped_by": equipped_by,
            "quantity": quantity,
            "id": self.id,
            "icon": self.icon,
            "description": self.description,
            "stats": self.stats,
            "value": self.value,
            "rarity": self.rarity
        }


@dataclass
class TalentData:
    """Represents a talent from the talent files."""
    id: str
    name: str
    level: int
    tier: str
    description: str
    action_type: str  # Attack, Magic, Spirit, Move, Inventory
    requirements: Dict[str, Any]
    effects: Dict[str, Any]
    cost: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TalentData':
        """Create TalentData from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            level=data['level'],
            tier=data['tier'],
            description=data['description'],
            action_type=data.get('action_type', 'Attack'),
            requirements=data.get('requirements', {}),
            effects=data.get('effects', {}),
            cost=data.get('cost', {})
        )


@dataclass
class AbilityData:
    """Represents an ability from the data files."""
    id: str
    name: str
    type: str  # Physical, Magical, Spiritual
    tier: str
    description: str
    effects: Dict[str, Any]
    requirements: Dict[str, Any]
    cost: Dict[str, int]  # AP, MP, etc.
    cooldown: int
    range: int
    area_of_effect: int
    icon: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AbilityData':
        """Create AbilityData from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            type=data['type'],
            tier=data['tier'],
            description=data['description'],
            effects=data.get('effects', {}),
            requirements=data.get('requirements', {}),
            cost=data.get('cost', {}),
            cooldown=data.get('cooldown', 0),
            range=data.get('range', 1),
            area_of_effect=data.get('area_of_effect', 0),
            icon=data['icon']
        )


class DataManager:
    """
    Manages loading and accessing game data.
    
    Features:
    - Item data loading and caching
    - Ability data management
    - Character/unit data handling
    - Zone/map data loading
    """
    
    def __init__(self):
        """Initialize the data manager."""
        self.asset_loader = get_asset_loader()
        
        # Data caches
        self._items: Dict[str, ItemData] = {}
        self._abilities: Dict[str, AbilityData] = {}
        self._talents: Dict[str, TalentData] = {}
        self._item_types: Dict[str, List[ItemData]] = {}
        
        # Load data
        self._load_all_data()
    
    def _load_all_data(self):
        """Load all game data from files."""
        self._load_items()
        self._load_abilities()
        self._load_talents()
        print("✅ DataManager loaded all game data")
    
    def _load_items(self):
        """Load item data from files."""
        # Load base items
        base_items_data = self.asset_loader.load_data("items/base_items.json")
        if base_items_data and 'items' in base_items_data:
            for item_dict in base_items_data['items']:
                item = ItemData.from_dict(item_dict)
                self._items[item.id] = item
                
                # Organize by type
                if item.type not in self._item_types:
                    self._item_types[item.type] = []
                self._item_types[item.type].append(item)
        
        print(f"✅ Loaded {len(self._items)} items from data files")
    
    def _load_abilities(self):
        """Load ability data from files."""
        # No abilities files exist yet - abilities are different from talents
        # When abilities are implemented, they would be loaded from abilities/base_abilities.json
        print(f"✅ Loaded {len(self._abilities)} abilities from data files (no ability files exist yet)")
    
    def _load_talents(self):
        """Load talents from talent files."""
        # Load talents from each talent tree file
        talent_files = [
            "abilities/physical_talents.json",
            "abilities/magical_talents.json", 
            "abilities/spiritual_talents.json"
        ]
        
        total_talents = 0
        for file_path in talent_files:
            talent_data = self.asset_loader.load_data(file_path)
            if talent_data and 'talents' in talent_data:
                for talent_dict in talent_data['talents']:
                    talent = TalentData.from_dict(talent_dict)
                    self._talents[talent.id] = talent
                    total_talents += 1
        
        print(f"✅ Loaded {total_talents} talents from data files")
    
    def get_item(self, item_id: str) -> Optional[ItemData]:
        """Get item data by ID."""
        return self._items.get(item_id)
    
    def get_items_by_type(self, item_type: str) -> List[ItemData]:
        """Get all items of a specific type."""
        return self._item_types.get(item_type, [])
    
    def get_all_items(self) -> List[ItemData]:
        """Get all items."""
        return list(self._items.values())
    
    def get_item_types(self) -> List[str]:
        """Get all available item types."""
        return list(self._item_types.keys())
    
    def get_ability(self, ability_id: str) -> Optional[AbilityData]:
        """Get ability data by ID."""
        return self._abilities.get(ability_id)
    
    def get_abilities_by_type(self, ability_type: str) -> List[AbilityData]:
        """Get all abilities of a specific type."""
        return [ability for ability in self._abilities.values() if ability.type == ability_type]
    
    def get_talent(self, talent_id: str) -> Optional[TalentData]:
        """Get talent data by ID."""
        return self._talents.get(talent_id)
    
    def get_talents_by_action_type(self, action_type: str) -> List[TalentData]:
        """Get all talents of a specific action type."""
        return [talent for talent in self._talents.values() if talent.action_type == action_type]
    
    def get_talents_by_tier(self, tier: str) -> List[TalentData]:
        """Get all talents of a specific tier."""
        return [talent for talent in self._talents.values() if talent.tier == tier]
    
    def get_all_talents(self) -> List[TalentData]:
        """Get all talents."""
        return list(self._talents.values())
    
    def get_ui_config(self) -> Optional[Dict[str, Any]]:
        """Get unified UI configuration data."""
        try:
            # Try new unified config first
            ui_config_data = self.asset_loader.load_data("ui/unified_ui_config.json")
            if ui_config_data:
                return ui_config_data
                
            # Fallback to old config files
            print("⚠️ Falling back to legacy UI config files")
            
            # Try character interface config
            char_config = self.asset_loader.load_data("ui/character_interface_config.json")
            old_ui_config = self.asset_loader.load_data("ui_config.json")
            
            # Merge legacy configs if available
            if char_config or old_ui_config:
                merged_config = {}
                if char_config:
                    merged_config.update(char_config)
                if old_ui_config:
                    merged_config.update(old_ui_config)
                return merged_config
                
            return None
        except Exception as e:
            print(f"Could not load UI config: {e}")
            return None
    
    def get_action_item_config(self) -> Dict[str, Any]:
        """Get action item configuration (talents, hotkeys, inventory items)."""
        ui_config = self.get_ui_config()
        if ui_config and 'action_items' in ui_config:
            return ui_config['action_items']
        
        # Fallback configuration
        return {
            "sizing": {"icon_scale": 0.06},
            "colors": {
                "Attack": "#FF0000",
                "Magic": "#0000FF", 
                "Spirit": "#FFFF00",
                "Move": "#00FF00",
                "Inventory": "#FFA500",
                "Empty": "#404040",
                "Default": "#FFFFFF"
            },
            "visual_effects": {
                "hover_brightness": 1.2,
                "selected_brightness": 1.4,
                "disabled_alpha": 0.5,
                "dragging_alpha": 0.7
            }
        }
    
    def create_sample_inventory(self, character_assignments: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """
        Create a sample inventory using loaded item data.
        
        Args:
            character_assignments: Dict mapping item_id to character name for equipped items
            
        Returns:
            List of items in inventory format
        """
        if character_assignments is None:
            character_assignments = {
                "iron_sword": "Hero",
                "leather_armor": "Hero", 
                "power_ring": "Mage"
            }
        
        inventory = []
        
        # Add some base items with different quantities
        item_quantities = {
            "iron_sword": 1,
            "steel_axe": 1,
            "magic_bow": 1,
            "spear": 1,
            "leather_armor": 1,
            "chain_mail": 1,
            "power_ring": 1,
            "health_potion": 5,
            "mana_potion": 3,
            "iron_ore": 10,
            "magic_crystal": 2,
            "dragon_scale": 1
        }
        
        for item_id, quantity in item_quantities.items():
            item_data = self.get_item(item_id)
            if item_data:
                equipped_by = character_assignments.get(item_id)
                inventory_item = item_data.to_inventory_format(equipped_by, quantity)
                inventory.append(inventory_item)
        
        return inventory
    
    def reload_data(self):
        """Reload all data from files."""
        self._items.clear()
        self._abilities.clear()
        self._talents.clear()
        self._item_types.clear()
        
        # Clear asset loader cache
        self.asset_loader.clear_cache('data')
        
        # Reload all data
        self._load_all_data()
        print("✅ Reloaded all game data")


# Global data manager instance
_data_manager: Optional[DataManager] = None


def get_data_manager() -> DataManager:
    """Get the global data manager instance."""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager()
    return _data_manager


def get_item(item_id: str) -> Optional[ItemData]:
    """Convenience function to get item data."""
    return get_data_manager().get_item(item_id)


def get_items_by_type(item_type: str) -> List[ItemData]:
    """Convenience function to get items by type."""
    return get_data_manager().get_items_by_type(item_type)


def create_sample_inventory(character_assignments: Dict[str, str] = None) -> List[Dict[str, Any]]:
    """Convenience function to create sample inventory."""
    return get_data_manager().create_sample_inventory(character_assignments)


# Unified UI helper functions
def get_action_item_scale() -> float:
    """Get standard scale for all action items (talents, hotkeys, inventory)."""
    return get_data_manager().get_action_item_config().get('sizing', {}).get('icon_scale', 0.06)

def get_action_item_color(action_type: str) -> str:
    """Get hex color for action type."""
    colors = get_data_manager().get_action_item_config().get('colors', {})
    return colors.get(action_type, colors.get('Default', '#FFFFFF'))

def convert_hex_to_ursina_color(hex_color: str):
    """Convert hex color to Ursina color object."""
    try:
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        from ursina import color
        return color.rgb(r, g, b)
    except:
        from ursina import color
        return color.white