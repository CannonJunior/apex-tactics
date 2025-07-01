"""
Damage System Components

Implements multi-layered damage types and damage calculation mechanics.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional
from core.ecs.component import BaseComponent


class AttackType(Enum):
    """Attack types that correspond to different defense layers"""
    PHYSICAL = "physical"
    MAGICAL = "magical" 
    SPIRITUAL = "spiritual"


@dataclass
class DamageResult:
    """Result of a damage calculation"""
    damage: int
    attack_type: AttackType
    penetration: int = 0
    critical: bool = False
    source_unit_id: Optional[int] = None
    target_unit_id: Optional[int] = None


class DamageComponent(BaseComponent):
    """
    Component for units that can deal damage.
    
    Supports multi-layered attack system with penetration mechanics.
    """
    
    def __init__(self, 
                 physical_power: int = 0,
                 magical_power: int = 0, 
                 spiritual_power: int = 0,
                 penetration: int = 0,
                 critical_chance: float = 0.05):
        """
        Initialize damage component.
        
        Args:
            physical_power: Base physical attack power
            magical_power: Base magical attack power  
            spiritual_power: Base spiritual attack power
            penetration: Armor penetration value
            critical_chance: Chance for critical hits (0.0-1.0)
        """
        super().__init__()
        self.physical_power = physical_power
        self.magical_power = magical_power
        self.spiritual_power = spiritual_power
        self.penetration = penetration
        self.critical_chance = critical_chance
    
    def get_attack_power(self, attack_type: AttackType) -> int:
        """Get attack power for specified attack type"""
        power_map = {
            AttackType.PHYSICAL: self.physical_power,
            AttackType.MAGICAL: self.magical_power,
            AttackType.SPIRITUAL: self.spiritual_power
        }
        return power_map[attack_type]
    
    def calculate_damage(self, attack_type: AttackType, target_defense: int) -> DamageResult:
        """
        Calculate damage against target defense using hybrid formula.
        
        Implements the advanced damage formula from the implementation guide:
        - If base_damage >= defense: final_damage = base_damage * 2 - defense
        - Otherwise: final_damage = (base_damage * base_damage) / defense
        - Apply penetration and minimum damage
        
        Args:
            attack_type: Type of attack being made
            target_defense: Target's defense value for this attack type
            
        Returns:
            DamageResult with calculated damage
        """
        import random
        
        base_damage = self.get_attack_power(attack_type)
        
        # Apply penetration to reduce effective defense
        effective_defense = max(0, target_defense - self.penetration)
        
        # Use hybrid damage formula to prevent zero damage
        if base_damage >= effective_defense:
            final_damage = base_damage * 2 - effective_defense
        else:
            if effective_defense > 0:
                final_damage = (base_damage * base_damage) / effective_defense
            else:
                final_damage = base_damage
        
        # Apply additional penetration scaling
        if effective_defense > 0:
            penetration_factor = final_damage / (final_damage + effective_defense)
            final_damage = final_damage * penetration_factor
        
        # Check for critical hit
        is_critical = random.random() < self.critical_chance
        if is_critical:
            final_damage *= 2.0
        
        # Ensure minimum damage of 1
        final_damage = max(1, int(final_damage))
        
        return DamageResult(
            damage=final_damage,
            attack_type=attack_type,
            penetration=self.penetration,
            critical=is_critical
        )
    
    def to_dict(self):
        """Serialize component to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'physical_power': self.physical_power,
            'magical_power': self.magical_power,
            'spiritual_power': self.spiritual_power,
            'penetration': self.penetration,
            'critical_chance': self.critical_chance
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data):
        """Deserialize component from dictionary"""
        return cls(
            physical_power=data.get('physical_power', 0),
            magical_power=data.get('magical_power', 0),
            spiritual_power=data.get('spiritual_power', 0),
            penetration=data.get('penetration', 0),
            critical_chance=data.get('critical_chance', 0.05)
        )