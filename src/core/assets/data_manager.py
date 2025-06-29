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
        self._item_types: Dict[str, List[ItemData]] = {}
        
        # Load data
        self._load_all_data()
    
    def _load_all_data(self):
        """Load all game data from files."""
        self._load_items()
        self._load_abilities()
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
        # Try to load abilities (file may not exist yet)
        abilities_data = self.asset_loader.load_data("abilities/base_abilities.json")
        if abilities_data and 'abilities' in abilities_data:
            for ability_dict in abilities_data['abilities']:
                ability = AbilityData.from_dict(ability_dict)
                self._abilities[ability.id] = ability
        
        print(f"✅ Loaded {len(self._abilities)} abilities from data files")
    
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