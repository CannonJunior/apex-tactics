"""
Unit Factory

Creates unit entities with proper ECS component composition.
Extracted from apex-tactics.py for better modularity.
"""

import random
from typing import Optional, Dict, Any

from core.ecs.entity import Entity as ECSEntity
from components.stats.attributes import AttributeStats
from components.gameplay.unit_type import UnitType, UnitTypeComponent
from components.movement.movement import MovementComponent
from components.combat.attack import AttackComponent
from components.combat.defense import DefenseComponent
from components.combat.damage import AttackType


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
        
        # Add unit type component
        unit_type_comp = UnitTypeComponent(unit_type)
        entity.add_component(unit_type_comp)
        
        # Apply type bonuses to stats
        for attr, bonus in unit_type_comp.get_all_bonuses().items():
            current_value = getattr(stats, attr, 0)
            setattr(stats, attr, current_value + bonus)
        
        # Invalidate derived stats cache to force recalculation with bonuses
        stats._invalidate_cache()
        
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