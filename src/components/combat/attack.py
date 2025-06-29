"""
Attack System Components

Implements attack actions and targeting mechanics.
"""

from dataclasses import dataclass
from typing import List, Optional
from core.ecs.component import BaseComponent
from core.math.vector import Vector3
from .damage import AttackType, DamageResult


@dataclass
class AttackTarget:
    """Represents a target for an attack"""
    unit_id: int
    position: Vector3
    distance: float


class AttackComponent(BaseComponent):
    """
    Component for units that can perform attacks.
    
    Supports single-target and area-of-effect attacks.
    """
    
    def __init__(self,
                 primary_attack_type: AttackType = AttackType.PHYSICAL,
                 attack_range: int = 1,
                 area_effect_radius: float = 0.0,
                 accuracy: float = 0.9,
                 can_friendly_fire: bool = True):
        """
        Initialize attack component.
        
        Args:
            primary_attack_type: Default attack type for this unit
            attack_range: Maximum attack range in grid units
            area_effect_radius: Radius for AoE attacks (0 = single target)
            accuracy: Base accuracy (0.0-1.0)
            can_friendly_fire: Whether AoE attacks can damage allies
        """
        super().__init__()
        self.primary_attack_type = primary_attack_type
        self.attack_range = attack_range
        self.area_effect_radius = area_effect_radius
        self.accuracy = accuracy
        self.can_friendly_fire = can_friendly_fire
        
        # Attack modifiers
        self.range_modifier = 0
        self.accuracy_modifier = 0.0
        self.damage_modifier = 1.0
    
    def get_effective_range(self) -> int:
        """Get total attack range including modifiers"""
        return max(1, self.attack_range + self.range_modifier)
    
    def get_effective_accuracy(self) -> float:
        """Get total accuracy including modifiers"""
        return max(0.0, min(1.0, self.accuracy + self.accuracy_modifier))
    
    def is_area_attack(self) -> bool:
        """Check if this is an area effect attack"""
        return self.area_effect_radius > 0.0
    
    def can_target_position(self, attacker_pos: Vector3, target_pos: Vector3) -> bool:
        """
        Check if a position is within attack range.
        
        Args:
            attacker_pos: Position of attacking unit
            target_pos: Position being targeted
            
        Returns:
            True if position is within range
        """
        distance = attacker_pos.distance_to(target_pos)
        return distance <= self.get_effective_range()
    
    def get_targets_in_area(self, center: Vector3, all_units: List[tuple]) -> List[AttackTarget]:
        """
        Get all potential targets within area effect radius.
        
        Args:
            center: Center position of area attack
            all_units: List of (unit_id, position) tuples
            
        Returns:
            List of AttackTarget objects within radius
        """
        if not self.is_area_attack():
            return []
        
        targets = []
        for unit_id, position in all_units:
            distance = center.distance_to(position)
            if distance <= self.area_effect_radius:
                targets.append(AttackTarget(
                    unit_id=unit_id,
                    position=position,
                    distance=distance
                ))
        
        return targets
    
    def calculate_area_damage_multiplier(self, distance: float) -> float:
        """
        Calculate damage multiplier based on distance from center.
        
        Implements falloff: max(0.1, 1 - (distance / radius * 0.9))
        
        Args:
            distance: Distance from area effect center
            
        Returns:
            Damage multiplier (0.1 to 1.0)
        """
        if not self.is_area_attack() or distance > self.area_effect_radius:
            return 0.0
        
        if distance == 0.0:
            return 1.0
        
        falloff = distance / self.area_effect_radius * 0.9
        return max(0.1, 1.0 - falloff)
    
    def add_range_modifier(self, modifier: int):
        """Add temporary range modifier"""
        self.range_modifier += modifier
    
    def add_accuracy_modifier(self, modifier: float):
        """Add temporary accuracy modifier"""
        self.accuracy_modifier += modifier
    
    def add_damage_modifier(self, modifier: float):
        """Add temporary damage modifier"""
        self.damage_modifier *= modifier
    
    def reset_modifiers(self):
        """Reset all temporary modifiers"""
        self.range_modifier = 0
        self.accuracy_modifier = 0.0
        self.damage_modifier = 1.0
    
    def to_dict(self):
        """Serialize component to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'primary_attack_type': self.primary_attack_type.value,
            'attack_range': self.attack_range,
            'area_effect_radius': self.area_effect_radius,
            'accuracy': self.accuracy,
            'can_friendly_fire': self.can_friendly_fire,
            'range_modifier': self.range_modifier,
            'accuracy_modifier': self.accuracy_modifier,
            'damage_modifier': self.damage_modifier
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data):
        """Deserialize component from dictionary"""
        return cls(
            primary_attack_type=AttackType(data.get('primary_attack_type', 'physical')),
            attack_range=data.get('attack_range', 1),
            area_effect_radius=data.get('area_effect_radius', 0.0),
            accuracy=data.get('accuracy', 0.9),
            can_friendly_fire=data.get('can_friendly_fire', True)
        )