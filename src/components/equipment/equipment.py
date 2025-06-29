"""
Equipment System with Five-Tier Progression

Implements the five-tier equipment system: Base, Enhanced, Enchanted, Superpowered, Metapowered.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional
from core.ecs.component import BaseComponent


class EquipmentTier(Enum):
    """Five-tier equipment progression system"""
    BASE = 1          # Basic equipment
    ENHANCED = 2      # Improved versions  
    ENCHANTED = 3     # Magical enhancements
    SUPERPOWERED = 4  # Extraordinary abilities
    METAPOWERED = 5   # Reality-bending properties


class EquipmentType(Enum):
    """Types of equipment that can be equipped"""
    WEAPON = "weapon"
    ARMOR = "armor"
    ACCESSORY = "accessory"
    CONSUMABLE = "consumable"


@dataclass
class EquipmentStats:
    """Statistics provided by equipment"""
    # Combat bonuses
    physical_attack: int = 0
    magical_attack: int = 0
    spiritual_attack: int = 0
    physical_defense: int = 0
    magical_defense: int = 0
    spiritual_defense: int = 0
    penetration: int = 0
    
    # Attribute bonuses
    strength: int = 0
    wisdom: int = 0
    wonder: int = 0
    worthy: int = 0
    faith: int = 0
    finesse: int = 0
    fortitude: int = 0
    speed: int = 0
    spirit: int = 0
    
    # Special properties
    critical_chance: float = 0.0
    accuracy_bonus: float = 0.0
    range_bonus: int = 0


class EquipmentComponent(BaseComponent):
    """
    Equipment component with tier-based scaling.
    
    Implements escalating complexity and power through five tiers.
    """
    
    def __init__(self,
                 name: str,
                 equipment_type: EquipmentType,
                 tier: EquipmentTier,
                 base_stats: EquipmentStats,
                 special_abilities: Optional[List[str]] = None):
        """
        Initialize equipment component.
        
        Args:
            name: Equipment name
            equipment_type: Type of equipment
            tier: Equipment tier (1-5)
            base_stats: Base statistical bonuses
            special_abilities: List of special ability names
        """
        super().__init__()
        self.name = name
        self.equipment_type = equipment_type
        self.tier = tier
        self.base_stats = base_stats
        self.special_abilities = special_abilities or []
        
        # Calculate tier-scaled stats
        self.effective_stats = self._calculate_tier_scaling()
        
        # Equipment durability and condition
        self.max_durability = self._calculate_max_durability()
        self.current_durability = self.max_durability
        self.is_equipped = False
    
    def _calculate_tier_scaling(self) -> EquipmentStats:
        """
        Calculate tier-scaled statistics.
        
        Implements exponential scaling:
        - Tier 1 (Base): 1.0x multiplier
        - Tier 2 (Enhanced): 1.5x multiplier  
        - Tier 3 (Enchanted): 2.5x multiplier
        - Tier 4 (Superpowered): 4.0x multiplier
        - Tier 5 (Metapowered): 6.5x multiplier
        """
        tier_multipliers = {
            EquipmentTier.BASE: 1.0,
            EquipmentTier.ENHANCED: 1.5,
            EquipmentTier.ENCHANTED: 2.5,
            EquipmentTier.SUPERPOWERED: 4.0,
            EquipmentTier.METAPOWERED: 6.5
        }
        
        multiplier = tier_multipliers[self.tier]
        
        # Scale all numeric stats
        scaled_stats = EquipmentStats()
        for field_name in scaled_stats.__dataclass_fields__:
            base_value = getattr(self.base_stats, field_name)
            
            if isinstance(base_value, int):
                setattr(scaled_stats, field_name, int(base_value * multiplier))
            elif isinstance(base_value, float):
                setattr(scaled_stats, field_name, base_value * multiplier)
        
        return scaled_stats
    
    def _calculate_max_durability(self) -> int:
        """Calculate maximum durability based on tier"""
        base_durability = 100
        tier_bonus = (self.tier.value - 1) * 50
        return base_durability + tier_bonus
    
    def get_tier_description(self) -> str:
        """Get human-readable tier description"""
        descriptions = {
            EquipmentTier.BASE: "Basic equipment with standard functionality",
            EquipmentTier.ENHANCED: "Improved equipment with better performance",
            EquipmentTier.ENCHANTED: "Magically enhanced equipment with special properties",
            EquipmentTier.SUPERPOWERED: "Extraordinary equipment with powerful abilities",
            EquipmentTier.METAPOWERED: "Reality-bending equipment with incredible power"
        }
        return descriptions[self.tier]
    
    def get_special_ability_power(self) -> float:
        """
        Get power multiplier for special abilities based on tier.
        
        Higher tiers have more powerful special abilities.
        """
        power_multipliers = {
            EquipmentTier.BASE: 1.0,
            EquipmentTier.ENHANCED: 1.3,
            EquipmentTier.ENCHANTED: 1.8,
            EquipmentTier.SUPERPOWERED: 2.5,
            EquipmentTier.METAPOWERED: 4.0
        }
        return power_multipliers[self.tier]
    
    def can_use_ability(self, ability_name: str) -> bool:
        """Check if equipment can use a specific ability"""
        return ability_name in self.special_abilities
    
    def take_damage(self, damage: int) -> bool:
        """
        Equipment takes durability damage.
        
        Args:
            damage: Durability damage amount
            
        Returns:
            True if equipment is still functional
        """
        self.current_durability = max(0, self.current_durability - damage)
        return self.current_durability > 0
    
    def repair(self, amount: int):
        """Repair equipment durability"""
        self.current_durability = min(self.max_durability, self.current_durability + amount)
    
    def get_condition_modifier(self) -> float:
        """
        Get effectiveness modifier based on current condition.
        
        Returns:
            Multiplier for equipment effectiveness (0.0-1.0)
        """
        if self.current_durability <= 0:
            return 0.0  # Broken equipment
        
        condition_ratio = self.current_durability / self.max_durability
        
        if condition_ratio >= 0.9:
            return 1.0  # Perfect condition
        elif condition_ratio >= 0.75:
            return 0.95  # Good condition
        elif condition_ratio >= 0.5:
            return 0.85  # Fair condition
        elif condition_ratio >= 0.25:
            return 0.7   # Poor condition
        else:
            return 0.5   # Very poor condition
    
    def get_effective_stats(self) -> EquipmentStats:
        """
        Get equipment stats modified by current condition.
        
        Returns:
            Equipment stats scaled by condition modifier
        """
        condition_modifier = self.get_condition_modifier()
        effective_stats = EquipmentStats()
        
        for field_name in effective_stats.__dataclass_fields__:
            base_value = getattr(self.effective_stats, field_name)
            
            if isinstance(base_value, int):
                setattr(effective_stats, field_name, int(base_value * condition_modifier))
            elif isinstance(base_value, float):
                setattr(effective_stats, field_name, base_value * condition_modifier)
        
        return effective_stats
    
    def get_equipment_info(self) -> dict:
        """Get comprehensive equipment information"""
        return {
            'name': self.name,
            'type': self.equipment_type.value,
            'tier': self.tier.name,
            'tier_description': self.get_tier_description(),
            'durability': f"{self.current_durability}/{self.max_durability}",
            'condition_modifier': self.get_condition_modifier(),
            'special_abilities': self.special_abilities,
            'ability_power': self.get_special_ability_power(),
            'base_stats': self.base_stats,
            'effective_stats': self.get_effective_stats(),
            'is_equipped': self.is_equipped
        }
    
    def to_dict(self):
        """Serialize component to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'name': self.name,
            'equipment_type': self.equipment_type.value,
            'tier': self.tier.value,
            'special_abilities': self.special_abilities,
            'max_durability': self.max_durability,
            'current_durability': self.current_durability,
            'is_equipped': self.is_equipped,
            # Store base stats as dict
            'base_stats': {
                field.name: getattr(self.base_stats, field.name)
                for field in self.base_stats.__dataclass_fields__.values()
            }
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data):
        """Deserialize component from dictionary"""
        # Reconstruct base stats
        base_stats = EquipmentStats()
        for field_name, field_value in data.get('base_stats', {}).items():
            setattr(base_stats, field_name, field_value)
        
        equipment = cls(
            name=data.get('name', ''),
            equipment_type=EquipmentType(data.get('equipment_type', 'weapon')),
            tier=EquipmentTier(data.get('tier', 1)),
            base_stats=base_stats,
            special_abilities=data.get('special_abilities', [])
        )
        
        # Restore durability and equipment state
        equipment.current_durability = data.get('current_durability', equipment.max_durability)
        equipment.is_equipped = data.get('is_equipped', False)
        
        return equipment