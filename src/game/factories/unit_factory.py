"""
Unit Factory

Creates unit entities with proper ECS component composition.
Extracted from apex-tactics.py for better modularity.
"""

import random
from typing import Optional, Dict, Any

from core.ecs.entity import Entity as ECSEntity
from components.stats.attributes import AttributeStats
from core.models.unit_types import UnitType
from components.movement.movement import MovementComponent
from components.combat.attack import AttackComponent
from components.combat.defense import DefenseComponent
from components.combat.damage import AttackType, DamageComponent


class UnitFactory:
    """Factory class for creating units with proper ECS composition."""
    
    @staticmethod
    def create_unit(name: str, unit_type: UnitType, x: int, y: int, 
                   wisdom: Optional[int] = None, wonder: Optional[int] = None, 
                   worthy: Optional[int] = None, faith: Optional[int] = None, 
                   finesse: Optional[int] = None, fortitude: Optional[int] = None, 
                   speed: Optional[int] = None, spirit: Optional[int] = None, 
                   strength: Optional[int] = None) -> ECSEntity:
        """
        Create a unit entity with modular components.
        
        Args:
            name: Unit name
            unit_type: UnitType enum value
            x, y: Grid position
            wisdom, wonder, worthy, faith, finesse, fortitude, speed, spirit, strength: 
                Optional attribute values (random if not provided)
                
        Returns:
            Configured ECS entity with all required components
        """
        # Create base attributes with random values if not provided
        base_attrs = {
            'wisdom': wisdom or random.randint(5, 15),
            'wonder': wonder or random.randint(5, 15),
            'worthy': worthy or random.randint(5, 15),
            'faith': faith or random.randint(5, 15),
            'finesse': finesse or random.randint(5, 15),
            'fortitude': fortitude or random.randint(5, 15),
            'speed': speed or random.randint(5, 15),
            'spirit': spirit or random.randint(5, 15),
            'strength': strength or random.randint(5, 15)
        }
        
        # Create ECS entity
        entity = ECSEntity()
        entity.name = name
        entity.x, entity.y = x, y  # Store position on entity
        
        # Add stats component
        stats = AttributeStats(**base_attrs)
        entity.add_component(stats)
        
        # TODO: Add unit type component when UnitTypeComponent is implemented
        # For now, just store unit_type on entity for reference
        entity.unit_type = unit_type
        
        # Add movement component
        movement_range = stats.speed // 2 + 2
        movement = MovementComponent(movement_range=movement_range)
        entity.add_component(movement)
        
        # Add combat components
        attack = AttackComponent(attack_range=1, area_effect_radius=0.0)
        entity.add_component(attack)
        
        # Initialize defense with calculated values
        defense = DefenseComponent(
            physical_defense=stats.derived_stats.get('physical_defense', 0),
            magical_defense=stats.derived_stats.get('magical_defense', 0),
            spiritual_defense=stats.derived_stats.get('spiritual_defense', 0)
        )
        entity.add_component(defense)
        
        # Add damage component with calculated attack values
        damage = DamageComponent(
            physical_power=stats.derived_stats.get('physical_attack', 0),
            magical_power=stats.derived_stats.get('magical_attack', 0),
            spiritual_power=stats.derived_stats.get('spiritual_attack', 0),
            critical_chance=stats.derived_stats.get('critical_chance', 5) / 100.0  # Convert to 0.0-1.0
        )
        entity.add_component(damage)
        
        return entity


# Standalone factory function for backwards compatibility
def create_unit_entity(name: str, unit_type: UnitType, x: int, y: int, 
                      wisdom: Optional[int] = None, wonder: Optional[int] = None, 
                      worthy: Optional[int] = None, faith: Optional[int] = None, 
                      finesse: Optional[int] = None, fortitude: Optional[int] = None, 
                      speed: Optional[int] = None, spirit: Optional[int] = None, 
                      strength: Optional[int] = None) -> ECSEntity:
    """
    Factory function to create a unit entity with modular components.
    
    This is the exact same function from apex-tactics.py, extracted for reusability.
    """
    return UnitFactory.create_unit(
        name, unit_type, x, y, wisdom, wonder, worthy, faith, 
        finesse, fortitude, speed, spirit, strength
    )