"""
Equipment Manager Component

Manages equipped items and applies their bonuses to units.
"""

from typing import Dict, List, Optional
from core.ecs.component import BaseComponent
from .equipment import EquipmentComponent, EquipmentType, EquipmentStats


class EquipmentManager(BaseComponent):
    """
    Component for managing a unit's equipped items.
    
    Handles equipment slots, bonuses calculation, and equipment management.
    """
    
    def __init__(self):
        super().__init__()
        
        # Equipment slots
        self.equipped_items: Dict[EquipmentType, EquipmentComponent] = {}
        self.inventory: List[EquipmentComponent] = []
        
        # Cached total bonuses (recalculated when equipment changes)
        self._cached_bonuses: Optional[EquipmentStats] = None
        self._bonuses_dirty = True
    
    def equip_item(self, equipment: EquipmentComponent) -> bool:
        """
        Equip an item in the appropriate slot.
        
        Args:
            equipment: Equipment to equip
            
        Returns:
            True if successfully equipped
        """
        if equipment.equipment_type == EquipmentType.CONSUMABLE:
            return False  # Can't equip consumables
        
        # Unequip current item in this slot if any
        if equipment.equipment_type in self.equipped_items:
            self.unequip_item(equipment.equipment_type)
        
        # Equip new item
        self.equipped_items[equipment.equipment_type] = equipment
        equipment.is_equipped = True
        
        # Remove from inventory if present
        if equipment in self.inventory:
            self.inventory.remove(equipment)
        
        self._bonuses_dirty = True
        return True
    
    def unequip_item(self, equipment_type: EquipmentType) -> Optional[EquipmentComponent]:
        """
        Unequip item from specified slot.
        
        Args:
            equipment_type: Type of equipment to unequip
            
        Returns:
            Unequipped item or None if slot was empty
        """
        if equipment_type not in self.equipped_items:
            return None
        
        equipment = self.equipped_items.pop(equipment_type)
        equipment.is_equipped = False
        
        # Add to inventory
        self.inventory.append(equipment)
        
        self._bonuses_dirty = True
        return equipment
    
    def add_to_inventory(self, equipment: EquipmentComponent):
        """Add equipment to inventory"""
        if equipment not in self.inventory:
            self.inventory.append(equipment)
    
    def remove_from_inventory(self, equipment: EquipmentComponent) -> bool:
        """
        Remove equipment from inventory.
        
        Args:
            equipment: Equipment to remove
            
        Returns:
            True if successfully removed
        """
        if equipment in self.inventory:
            self.inventory.remove(equipment)
            return True
        return False
    
    def get_total_bonuses(self) -> EquipmentStats:
        """
        Calculate total equipment bonuses from all equipped items.
        
        Returns:
            Combined equipment bonuses
        """
        if not self._bonuses_dirty and self._cached_bonuses:
            return self._cached_bonuses
        
        total_bonuses = EquipmentStats()
        
        for equipment in self.equipped_items.values():
            effective_stats = equipment.get_effective_stats()
            
            # Sum all numeric bonuses
            for field_name in total_bonuses.__dataclass_fields__:
                current_value = getattr(total_bonuses, field_name)
                equipment_value = getattr(effective_stats, field_name)
                
                if isinstance(current_value, (int, float)):
                    setattr(total_bonuses, field_name, current_value + equipment_value)
        
        self._cached_bonuses = total_bonuses
        self._bonuses_dirty = False
        return total_bonuses
    
    def get_equipped_item(self, equipment_type: EquipmentType) -> Optional[EquipmentComponent]:
        """Get currently equipped item of specified type"""
        return self.equipped_items.get(equipment_type)
    
    def get_all_equipped_items(self) -> List[EquipmentComponent]:
        """Get list of all currently equipped items"""
        return list(self.equipped_items.values())
    
    def get_inventory_items(self) -> List[EquipmentComponent]:
        """Get list of all inventory items"""
        return self.inventory.copy()
    
    def has_special_ability(self, ability_name: str) -> bool:
        """
        Check if any equipped item provides a special ability.
        
        Args:
            ability_name: Name of ability to check
            
        Returns:
            True if any equipped item has this ability
        """
        for equipment in self.equipped_items.values():
            if equipment.can_use_ability(ability_name):
                return True
        return False
    
    def get_all_special_abilities(self) -> List[str]:
        """Get list of all special abilities from equipped items"""
        abilities = []
        for equipment in self.equipped_items.values():
            abilities.extend(equipment.special_abilities)
        return list(set(abilities))  # Remove duplicates
    
    def calculate_equipment_value(self) -> int:
        """Calculate total value of all equipment (equipped + inventory)"""
        total_value = 0
        
        # Value calculation based on tier and stats
        for equipment in list(self.equipped_items.values()) + self.inventory:
            base_value = equipment.tier.value * 100
            condition_modifier = equipment.get_condition_modifier()
            total_value += int(base_value * condition_modifier)
        
        return total_value
    
    def take_equipment_damage(self, damage: int) -> List[str]:
        """
        Apply damage to random equipped items.
        
        Args:
            damage: Amount of durability damage
            
        Returns:
            List of equipment names that were broken
        """
        import random
        
        broken_items = []
        
        if not self.equipped_items:
            return broken_items
        
        # Randomly select an equipped item to take damage
        equipment = random.choice(list(self.equipped_items.values()))
        
        if not equipment.take_damage(damage):
            # Equipment was broken
            broken_items.append(equipment.name)
            self.unequip_item(equipment.equipment_type)
        
        self._bonuses_dirty = True
        return broken_items
    
    def repair_all_equipment(self, repair_amount: int):
        """Repair all equipment by specified amount"""
        for equipment in list(self.equipped_items.values()) + self.inventory:
            equipment.repair(repair_amount)
        
        self._bonuses_dirty = True
    
    def get_equipment_summary(self) -> dict:
        """Get comprehensive equipment summary"""
        return {
            'equipped_items': {
                eq_type.value: equipment.get_equipment_info() 
                for eq_type, equipment in self.equipped_items.items()
            },
            'inventory_count': len(self.inventory),
            'total_value': self.calculate_equipment_value(),
            'special_abilities': self.get_all_special_abilities(),
            'total_bonuses': self.get_total_bonuses(),
            'equipment_condition': {
                equipment.name: equipment.get_condition_modifier()
                for equipment in self.get_all_equipped_items()
            }
        }
    
    def to_dict(self):
        """Serialize component to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'equipped_items': {
                eq_type.value: equipment.to_dict()
                for eq_type, equipment in self.equipped_items.items()
            },
            'inventory': [equipment.to_dict() for equipment in self.inventory]
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data):
        """Deserialize component from dictionary"""
        manager = cls()
        
        # Restore equipped items
        for eq_type_str, eq_data in data.get('equipped_items', {}).items():
            eq_type = EquipmentType(eq_type_str)
            equipment = EquipmentComponent.from_dict(eq_data)
            manager.equipped_items[eq_type] = equipment
        
        # Restore inventory
        for eq_data in data.get('inventory', []):
            equipment = EquipmentComponent.from_dict(eq_data)
            manager.inventory.append(equipment)
        
        return manager