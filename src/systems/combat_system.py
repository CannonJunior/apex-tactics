"""
Combat System Implementation

Handles combat calculations, area effects, and damage resolution.
"""

import random
from typing import List, Optional, Tuple
from core.ecs.system import BaseSystem
from core.ecs.entity import Entity
from core.ecs.component import Transform
from core.math.vector import Vector3
from components.combat.damage import DamageComponent, DamageResult, AttackType
from components.combat.defense import DefenseComponent
from components.combat.attack import AttackComponent, AttackTarget
from components.stats.attributes import AttributeStats


class AreaEffectSystem:
    """
    Handles complex area damage calculations with friendly fire support.
    
    Implements the area effect resolution system from the implementation guide.
    """
    
    def calculate_area_damage(self, 
                            origin: Vector3, 
                            radius: float,
                            base_damage: int,
                            attack_type: AttackType,
                            caster_id: int,
                            all_units: List[Tuple[int, Entity]],
                            friendly_fire_enabled: bool = True) -> List[DamageResult]:
        """
        Calculate area damage for all units within radius.
        
        Args:
            origin: Center point of area effect
            radius: Effect radius
            base_damage: Base damage amount
            attack_type: Type of damage being dealt
            caster_id: ID of unit casting the effect
            all_units: List of (unit_id, entity) tuples
            friendly_fire_enabled: Whether to damage friendly units
            
        Returns:
            List of DamageResult objects for affected units
        """
        results = []
        
        for unit_id, unit_entity in all_units:
            transform = unit_entity.get_component(Transform)
            if not transform:
                continue
            
            # Calculate distance from effect center
            distance = origin.distance_to(transform.position)
            if distance > radius:
                continue  # Unit is outside effect radius
            
            # Calculate damage multiplier based on distance
            damage_multiplier = max(0.1, 1 - (distance / radius * 0.9))
            damage = int(base_damage * damage_multiplier)
            
            # Handle friendly fire
            if unit_id != caster_id:  # Don't damage self
                is_friendly = self._is_friendly_unit(caster_id, unit_id, all_units)
                
                if is_friendly:
                    if self._has_precision_casting(caster_id, all_units):
                        damage = 0  # Avoid friendly fire with precise casting
                    elif friendly_fire_enabled:
                        damage = int(damage * 0.5)  # 50% friendly fire damage
                    else:
                        damage = 0  # No friendly fire
            else:
                damage = 0  # Don't damage self
            
            if damage > 0:
                results.append(DamageResult(
                    damage=damage,
                    attack_type=attack_type,
                    source_unit_id=caster_id,
                    target_unit_id=unit_id
                ))
        
        return results
    
    def _is_friendly_unit(self, caster_id: int, target_id: int, all_units: List[Tuple[int, Entity]]) -> bool:
        """
        Determine if two units are friendly.
        
        For now, implements simple team-based logic.
        Can be expanded with faction systems later.
        """
        # TODO: Implement proper faction/team system
        # For now, assume all units are friendly (placeholder)
        return True
    
    def _has_precision_casting(self, caster_id: int, all_units: List[Tuple[int, Entity]]) -> bool:
        """
        Check if caster has precision casting ability.
        
        TODO: Implement proper ability system
        """
        # Placeholder - can be expanded with ability system
        return False


class CombatSystem(BaseSystem):
    """
    Main combat system for handling damage calculations and resolution.
    """
    
    def __init__(self):
        super().__init__()
        self.area_effect_system = AreaEffectSystem()
    
    def get_required_components(self):
        """CombatSystem doesn't require specific components - it provides utilities"""
        return set()
    
    def update(self, delta_time, entities):
        """CombatSystem doesn't need regular updates - it provides on-demand calculations"""
        pass
    
    def calculate_damage(self, attacker: Entity, target: Entity, attack_type: AttackType) -> Optional[DamageResult]:
        """
        Calculate damage between two units using multi-layered defense.
        
        Args:
            attacker: Entity performing the attack
            target: Entity being attacked
            attack_type: Type of attack being performed
            
        Returns:
            DamageResult or None if attack fails
        """
        # Get attacker's damage component
        damage_component = attacker.get_component(DamageComponent)
        if not damage_component:
            return None
        
        # Get target's defense component
        defense_component = target.get_component(DefenseComponent)
        target_defense = defense_component.get_defense_value(attack_type) if defense_component else 0
        
        # Calculate damage using the damage component
        damage_result = damage_component.calculate_damage(attack_type, target_defense)
        
        # Set source and target IDs
        damage_result.source_unit_id = attacker.id
        damage_result.target_unit_id = target.id
        
        return damage_result
    
    def can_attack(self, attacker: Entity, target: Entity) -> bool:
        """
        Check if attacker can attack target.
        
        Args:
            attacker: Entity attempting to attack
            target: Potential target entity
            
        Returns:
            True if attack is possible
        """
        attack_component = attacker.get_component(AttackComponent)
        if not attack_component:
            return False
        
        # Get positions
        attacker_transform = attacker.get_component(Transform)
        target_transform = target.get_component(Transform)
        
        if not attacker_transform or not target_transform:
            return False
        
        # Check range
        return attack_component.can_target_position(
            attacker_transform.position,
            target_transform.position
        )
    
    def perform_area_attack(self, 
                          attacker: Entity,
                          target_position: Vector3,
                          all_units: List[Tuple[int, Entity]]) -> List[DamageResult]:
        """
        Perform an area of effect attack.
        
        Args:
            attacker: Entity performing the attack
            target_position: Center of area effect
            all_units: All units that could be affected
            
        Returns:
            List of damage results for all affected units
        """
        attack_component = attacker.get_component(AttackComponent)
        damage_component = attacker.get_component(DamageComponent)
        
        if not attack_component or not damage_component or not attack_component.is_area_attack():
            return []
        
        # Get base damage for primary attack type
        base_damage = damage_component.get_attack_power(attack_component.primary_attack_type)
        
        # Calculate area damage
        return self.area_effect_system.calculate_area_damage(
            origin=target_position,
            radius=attack_component.area_effect_radius,
            base_damage=base_damage,
            attack_type=attack_component.primary_attack_type,
            caster_id=attacker.id,
            all_units=all_units,
            friendly_fire_enabled=attack_component.can_friendly_fire
        )
    
    def apply_damage(self, target: Entity, damage_result: DamageResult) -> bool:
        """
        Apply damage to target entity.
        
        Args:
            target: Entity receiving damage
            damage_result: Damage calculation result
            
        Returns:
            True if target is still alive after damage
        """
        # Get target's attribute component for HP
        attributes = target.get_component(AttributeStats)
        if not attributes:
            return True
        
        # Apply damage to HP
        attributes.current_hp = max(0, attributes.current_hp - damage_result.damage)
        
        # Return whether target is still alive
        return attributes.current_hp > 0
    
    def update(self, delta_time: float):
        """Update combat system (placeholder for future tick-based combat)"""
        pass