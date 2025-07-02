"""
Equipment Component

Manages unit equipment, item bonuses, and equipment tier effects
following the Apex Tactics five-tier equipment system.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from ...core.ecs import Component


class EquipmentTier(str, Enum):
    """Five-tier equipment system"""
    BASE = "base"              # 1.0x multiplier
    ENHANCED = "enhanced"      # 1.4x multiplier  
    ENCHANTED = "enchanted"    # 2.0x multiplier
    SUPERPOWERED = "superpowered"  # 3.0x multiplier
    METAPOWERED = "metapowered"    # 4.5x multiplier


class EquipmentSlot(str, Enum):
    """Equipment slots"""
    WEAPON = "weapon"
    ARMOR = "armor" 
    ACCESSORY1 = "accessory1"
    ACCESSORY2 = "accessory2"
    CONSUMABLE1 = "consumable1"
    CONSUMABLE2 = "consumable2"


class DamageType(str, Enum):
    """Damage types for equipment bonuses"""
    PHYSICAL = "physical"
    MAGICAL = "magical"
    SPIRITUAL = "spiritual"


@dataclass
class EquipmentItem:
    """Individual equipment item"""
    item_id: str
    name: str
    tier: EquipmentTier
    slot: EquipmentSlot
    
    # Base stats
    attack_bonus: int = 0
    defense_bonus: int = 0
    accuracy_bonus: float = 0.0
    critical_bonus: float = 0.0
    
    # Attribute bonuses
    attribute_bonuses: Dict[str, int] = field(default_factory=dict)
    
    # Special properties
    damage_types: List[DamageType] = field(default_factory=list)
    special_abilities: List[str] = field(default_factory=list)
    status_immunities: List[str] = field(default_factory=list)
    
    # Tier-specific properties
    ability_slots: int = 1  # Increases with tier
    is_sentient: bool = False  # True for METAPOWERED items
    
    # Durability and usage
    max_durability: int = 100
    current_durability: int = 100
    uses_remaining: int = -1  # -1 for unlimited use
    
    def get_tier_multiplier(self) -> float:
        """Get damage/stat multiplier based on tier"""
        multipliers = {
            EquipmentTier.BASE: 1.0,
            EquipmentTier.ENHANCED: 1.4,
            EquipmentTier.ENCHANTED: 2.0,
            EquipmentTier.SUPERPOWERED: 3.0,
            EquipmentTier.METAPOWERED: 4.5
        }
        return multipliers.get(self.tier, 1.0)
    
    def get_effective_attack_bonus(self) -> int:
        """Get attack bonus with tier multiplier"""
        return int(self.attack_bonus * self.get_tier_multiplier())
    
    def get_effective_defense_bonus(self) -> int:
        """Get defense bonus with tier multiplier"""
        return int(self.defense_bonus * self.get_tier_multiplier())
    
    def get_ability_slots(self) -> int:
        """Get number of ability slots based on tier"""
        slots_by_tier = {
            EquipmentTier.BASE: 1,
            EquipmentTier.ENHANCED: 1,
            EquipmentTier.ENCHANTED: 2,
            EquipmentTier.SUPERPOWERED: 3,
            EquipmentTier.METAPOWERED: 4
        }
        return slots_by_tier.get(self.tier, 1)
    
    def is_broken(self) -> bool:
        """Check if item is broken"""
        return self.current_durability <= 0
    
    def use_item(self) -> bool:
        """Use item (for consumables)"""
        if self.uses_remaining == 0:
            return False
        
        if self.uses_remaining > 0:
            self.uses_remaining -= 1
        
        return True
    
    def repair(self, amount: int = None):
        """Repair item durability"""
        if amount is None:
            self.current_durability = self.max_durability
        else:
            self.current_durability = min(
                self.max_durability, 
                self.current_durability + amount
            )


@dataclass
class EquipmentComponent(Component):
    """Component for unit equipment management"""
    
    # Equipment slots
    equipped_items: Dict[EquipmentSlot, Optional[EquipmentItem]] = field(
        default_factory=lambda: {slot: None for slot in EquipmentSlot}
    )
    
    # Equipment bonuses (calculated from equipped items)
    total_attack_bonus: int = 0
    total_defense_bonus: int = 0
    total_accuracy_bonus: float = 0.0
    total_critical_bonus: float = 0.0
    
    # Attribute bonuses from equipment
    attribute_bonuses: Dict[str, int] = field(default_factory=dict)
    
    # Special equipment effects
    active_abilities: List[str] = field(default_factory=list)
    status_immunities: List[str] = field(default_factory=list)
    damage_resistances: Dict[DamageType, float] = field(default_factory=dict)
    
    # Equipment state
    needs_recalculation: bool = True
    
    def equip_item(self, item: EquipmentItem) -> bool:
        """Equip an item"""
        if item.slot not in self.equipped_items:
            return False
        
        # Unequip current item if any
        current_item = self.equipped_items[item.slot]
        if current_item:
            self.unequip_item(item.slot)
        
        # Equip new item
        self.equipped_items[item.slot] = item
        self.needs_recalculation = True
        
        return True
    
    def unequip_item(self, slot: EquipmentSlot) -> Optional[EquipmentItem]:
        """Unequip item from slot"""
        item = self.equipped_items.get(slot)
        if item:
            self.equipped_items[slot] = None
            self.needs_recalculation = True
        
        return item
    
    def get_equipped_item(self, slot: EquipmentSlot) -> Optional[EquipmentItem]:
        """Get item equipped in slot"""
        return self.equipped_items.get(slot)
    
    def has_item_equipped(self, slot: EquipmentSlot) -> bool:
        """Check if slot has item equipped"""
        return self.equipped_items.get(slot) is not None
    
    def calculate_bonuses(self):
        """Recalculate all equipment bonuses"""
        if not self.needs_recalculation:
            return
        
        # Reset bonuses
        self.total_attack_bonus = 0
        self.total_defense_bonus = 0
        self.total_accuracy_bonus = 0.0
        self.total_critical_bonus = 0.0
        self.attribute_bonuses.clear()
        self.active_abilities.clear()
        self.status_immunities.clear()
        self.damage_resistances.clear()
        
        # Sum bonuses from all equipped items
        for item in self.equipped_items.values():
            if item and not item.is_broken():
                self._apply_item_bonuses(item)
        
        self.needs_recalculation = False
    
    def _apply_item_bonuses(self, item: EquipmentItem):
        """Apply bonuses from a single item"""
        # Basic stat bonuses
        self.total_attack_bonus += item.get_effective_attack_bonus()
        self.total_defense_bonus += item.get_effective_defense_bonus()
        self.total_accuracy_bonus += item.accuracy_bonus
        self.total_critical_bonus += item.critical_bonus
        
        # Attribute bonuses
        for attr, bonus in item.attribute_bonuses.items():
            effective_bonus = int(bonus * item.get_tier_multiplier())
            self.attribute_bonuses[attr] = self.attribute_bonuses.get(attr, 0) + effective_bonus
        
        # Special abilities
        self.active_abilities.extend(item.special_abilities)
        
        # Status immunities
        self.status_immunities.extend(item.status_immunities)
        
        # Damage resistances (higher tier items provide better resistance)
        for damage_type in item.damage_types:
            resistance = 0.1 * item.get_tier_multiplier()  # 10% per tier multiplier
            current_resistance = self.damage_resistances.get(damage_type, 0.0)
            self.damage_resistances[damage_type] = min(0.9, current_resistance + resistance)
    
    def get_damage_multiplier(self) -> float:
        """Get overall damage multiplier from equipment"""
        # Calculate average tier multiplier
        multipliers = []
        for item in self.equipped_items.values():
            if item and not item.is_broken():
                multipliers.append(item.get_tier_multiplier())
        
        if not multipliers:
            return 1.0
        
        # Use geometric mean for balanced scaling
        product = 1.0
        for mult in multipliers:
            product *= mult
        
        return product ** (1.0 / len(multipliers))
    
    def get_accuracy_bonus(self) -> float:
        """Get total accuracy bonus"""
        self.calculate_bonuses()
        return self.total_accuracy_bonus
    
    def get_critical_bonus(self) -> float:
        """Get total critical hit bonus"""
        self.calculate_bonuses()
        return self.total_critical_bonus
    
    def get_defense_bonus(self, damage_type: DamageType) -> int:
        """Get defense bonus against specific damage type"""
        self.calculate_bonuses()
        
        base_defense = self.total_defense_bonus
        resistance = self.damage_resistances.get(damage_type, 0.0)
        
        # Apply resistance as additional defense
        return int(base_defense * (1.0 + resistance))
    
    def get_attribute_bonus(self, attribute: str) -> int:
        """Get bonus to specific attribute"""
        self.calculate_bonuses()
        return self.attribute_bonuses.get(attribute, 0)
    
    def has_ability(self, ability_name: str) -> bool:
        """Check if has specific ability from equipment"""
        self.calculate_bonuses()
        return ability_name in self.active_abilities
    
    def is_immune_to_status(self, status_effect: str) -> bool:
        """Check if immune to status effect"""
        self.calculate_bonuses()
        return status_effect in self.status_immunities
    
    def get_highest_tier_item(self) -> Optional[EquipmentItem]:
        """Get highest tier equipped item"""
        highest_item = None
        highest_multiplier = 0.0
        
        for item in self.equipped_items.values():
            if item and not item.is_broken():
                multiplier = item.get_tier_multiplier()
                if multiplier > highest_multiplier:
                    highest_multiplier = multiplier
                    highest_item = item
        
        return highest_item
    
    def get_sentient_items(self) -> List[EquipmentItem]:
        """Get all sentient (METAPOWERED) items"""
        sentient_items = []
        for item in self.equipped_items.values():
            if item and item.is_sentient and not item.is_broken():
                sentient_items.append(item)
        
        return sentient_items
    
    def repair_all_items(self):
        """Repair all equipped items"""
        for item in self.equipped_items.values():
            if item:
                item.repair()
    
    def get_equipment_value(self) -> int:
        """Get total value of equipped items"""
        total_value = 0
        tier_values = {
            EquipmentTier.BASE: 100,
            EquipmentTier.ENHANCED: 300,
            EquipmentTier.ENCHANTED: 800,
            EquipmentTier.SUPERPOWERED: 2000,
            EquipmentTier.METAPOWERED: 5000
        }
        
        for item in self.equipped_items.values():
            if item:
                base_value = tier_values.get(item.tier, 100)
                durability_factor = item.current_durability / item.max_durability
                total_value += int(base_value * durability_factor)
        
        return total_value
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize component to dictionary"""
        equipped_data = {}
        for slot, item in self.equipped_items.items():
            if item:
                equipped_data[slot.value] = {
                    "item_id": item.item_id,
                    "name": item.name,
                    "tier": item.tier.value,
                    "slot": item.slot.value,
                    "attack_bonus": item.attack_bonus,
                    "defense_bonus": item.defense_bonus,
                    "accuracy_bonus": item.accuracy_bonus,
                    "critical_bonus": item.critical_bonus,
                    "attribute_bonuses": item.attribute_bonuses,
                    "special_abilities": item.special_abilities,
                    "status_immunities": item.status_immunities,
                    "current_durability": item.current_durability,
                    "max_durability": item.max_durability,
                    "uses_remaining": item.uses_remaining,
                    "is_sentient": item.is_sentient
                }
        
        return {
            "equipped_items": equipped_data,
            "total_attack_bonus": self.total_attack_bonus,
            "total_defense_bonus": self.total_defense_bonus,
            "total_accuracy_bonus": self.total_accuracy_bonus,
            "total_critical_bonus": self.total_critical_bonus,
            "attribute_bonuses": self.attribute_bonuses,
            "active_abilities": self.active_abilities,
            "status_immunities": self.status_immunities
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Deserialize component from dictionary"""
        equipped_data = data.get("equipped_items", {})
        self.equipped_items = {slot: None for slot in EquipmentSlot}
        
        for slot_name, item_data in equipped_data.items():
            slot = EquipmentSlot(slot_name)
            item = EquipmentItem(
                item_id=item_data["item_id"],
                name=item_data["name"],
                tier=EquipmentTier(item_data["tier"]),
                slot=EquipmentSlot(item_data["slot"]),
                attack_bonus=item_data.get("attack_bonus", 0),
                defense_bonus=item_data.get("defense_bonus", 0),
                accuracy_bonus=item_data.get("accuracy_bonus", 0.0),
                critical_bonus=item_data.get("critical_bonus", 0.0),
                attribute_bonuses=item_data.get("attribute_bonuses", {}),
                special_abilities=item_data.get("special_abilities", []),
                status_immunities=item_data.get("status_immunities", []),
                current_durability=item_data.get("current_durability", 100),
                max_durability=item_data.get("max_durability", 100),
                uses_remaining=item_data.get("uses_remaining", -1),
                is_sentient=item_data.get("is_sentient", False)
            )
            self.equipped_items[slot] = item
        
        self.total_attack_bonus = data.get("total_attack_bonus", 0)
        self.total_defense_bonus = data.get("total_defense_bonus", 0)
        self.total_accuracy_bonus = data.get("total_accuracy_bonus", 0.0)
        self.total_critical_bonus = data.get("total_critical_bonus", 0.0)
        self.attribute_bonuses = data.get("attribute_bonuses", {})
        self.active_abilities = data.get("active_abilities", [])
        self.status_immunities = data.get("status_immunities", [])
        
        self.needs_recalculation = True