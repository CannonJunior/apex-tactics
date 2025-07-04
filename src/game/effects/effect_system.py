"""
Unified Effect System

Base classes for all game effects that can be applied to units, terrain, or game state.
Replaces separate damage, healing, buff, and debuff systems with unified approach.
"""

from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod
from enum import Enum
import json


class EffectType(Enum):
    """Types of effects that can be applied."""
    DAMAGE = "damage"
    HEALING = "healing"
    STAT_MODIFIER = "stat_modifier"
    STATUS_EFFECT = "status_effect"
    MOVEMENT = "movement"
    RESOURCE_CHANGE = "resource_change"
    TERRAIN_CHANGE = "terrain_change"
    SPECIAL = "special"


class EffectTarget(Enum):
    """What can be targeted by effects."""
    UNIT = "unit"
    TILE = "tile"
    AREA = "area"
    GLOBAL = "global"


class DamageType(Enum):
    """Types of damage for damage effects."""
    PHYSICAL = "physical"
    MAGICAL = "magical"
    SPIRITUAL = "spiritual"
    TRUE = "true"  # Ignores all defenses


class ResourceType(Enum):
    """Types of resources that can be modified."""
    HP = "hp"
    MP = "mp"
    AP = "ap"
    RAGE = "rage"
    KWAN = "kwan"


class Effect(ABC):
    """
    Base class for all game effects.
    
    Effects are applied to targets and can modify game state, unit stats,
    or trigger other game mechanics.
    """
    
    def __init__(self, effect_type: EffectType, magnitude: Union[int, float], 
                 duration: int = 0, source_id: str = None):
        """
        Initialize effect.
        
        Args:
            effect_type: Type of effect
            magnitude: Strength/amount of effect
            duration: How long effect lasts (0 = instant)
            source_id: ID of the source (action, talent, item)
        """
        self.type = effect_type
        self.magnitude = magnitude
        self.duration = duration
        self.source_id = source_id
        self.target_type = EffectTarget.UNIT  # Default target type
        
        # Effect metadata
        self.description = ""
        self.visual_effect = None
        self.sound_effect = None
        
        # Validation and requirements
        self.requirements = {}
        self.restrictions = {}
    
    @abstractmethod
    def can_apply(self, target: Any, context: Dict[str, Any]) -> bool:
        """
        Check if effect can be applied to target.
        
        Args:
            target: Target to apply effect to
            context: Game context (battle state, etc.)
            
        Returns:
            True if effect can be applied
        """
        pass
    
    @abstractmethod
    def apply(self, target: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply effect to target.
        
        Args:
            target: Target to apply effect to
            context: Game context
            
        Returns:
            Result dictionary with effect outcomes
        """
        pass
    
    def get_preview_text(self, target: Any = None) -> str:
        """Get human-readable preview of effect."""
        return self.description or f"{self.type.value}: {self.magnitude}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize effect to dictionary."""
        return {
            'type': self.type.value,
            'magnitude': self.magnitude,
            'duration': self.duration,
            'source_id': self.source_id,
            'target_type': self.target_type.value,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Effect':
        """Create effect from dictionary."""
        effect_type = EffectType(data['type'])
        magnitude = data['magnitude']
        duration = data.get('duration', 0)
        source_id = data.get('source_id')
        
        # Create appropriate effect subclass based on type
        if effect_type == EffectType.DAMAGE:
            return DamageEffect(magnitude, duration, source_id, 
                               DamageType(data.get('damage_type', 'physical')))
        elif effect_type == EffectType.HEALING:
            return HealingEffect(magnitude, duration, source_id)
        elif effect_type == EffectType.STAT_MODIFIER:
            return StatModifierEffect(data.get('stat_name'), magnitude, duration, source_id)
        elif effect_type == EffectType.RESOURCE_CHANGE:
            return ResourceEffect(ResourceType(data.get('resource_type', 'mp')), magnitude, duration, source_id)
        else:
            # Generic effect for unknown types
            effect = cls.__new__(cls)
            effect.__init__(effect_type, magnitude, duration, source_id)
            return effect


class DamageEffect(Effect):
    """Effect that deals damage to units."""
    
    def __init__(self, damage: int, duration: int = 0, source_id: str = None, 
                 damage_type: DamageType = DamageType.PHYSICAL):
        super().__init__(EffectType.DAMAGE, damage, duration, source_id)
        self.damage_type = damage_type
        self.description = f"Deals {damage} {damage_type.value} damage"
    
    def can_apply(self, target: Any, context: Dict[str, Any]) -> bool:
        """Check if damage can be applied to target."""
        # Must be a unit with HP
        if not hasattr(target, 'hp') or not hasattr(target, 'alive'):
            return False
        
        # Must be alive
        if not target.alive:
            return False
            
        return True
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply damage to target."""
        if not self.can_apply(target, context):
            return {'success': False, 'reason': 'Invalid target for damage'}
        
        # Calculate actual damage based on defenses
        actual_damage = self._calculate_damage(target)
        
        # Apply damage
        old_hp = target.hp
        target.take_damage(actual_damage, self.damage_type)
        damage_dealt = old_hp - target.hp
        
        return {
            'success': True,
            'damage_dealt': damage_dealt,
            'target_hp': target.hp,
            'target_alive': target.alive,
            'damage_type': self.damage_type.value
        }
    
    def _calculate_damage(self, target: Any) -> int:
        """Calculate actual damage after defenses."""
        base_damage = self.magnitude
        
        if self.damage_type == DamageType.TRUE:
            return base_damage
        
        # Get appropriate defense
        defense = 0
        if self.damage_type == DamageType.PHYSICAL and hasattr(target, 'physical_defense'):
            defense = target.physical_defense
        elif self.damage_type == DamageType.MAGICAL and hasattr(target, 'magical_defense'):
            defense = target.magical_defense
        elif self.damage_type == DamageType.SPIRITUAL and hasattr(target, 'spiritual_defense'):
            defense = target.spiritual_defense
        
        # Apply defense (minimum 1 damage)
        actual_damage = max(1, base_damage - defense)
        return actual_damage


class HealingEffect(Effect):
    """Effect that restores HP to units."""
    
    def __init__(self, healing: int, duration: int = 0, source_id: str = None):
        super().__init__(EffectType.HEALING, healing, duration, source_id)
        self.description = f"Restores {healing} HP"
    
    def can_apply(self, target: Any, context: Dict[str, Any]) -> bool:
        """Check if healing can be applied to target."""
        # Must be a unit with HP
        if not hasattr(target, 'hp') or not hasattr(target, 'max_hp'):
            return False
        
        # Must be alive and not at full HP
        if not getattr(target, 'alive', True) or target.hp >= target.max_hp:
            return False
            
        return True
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply healing to target."""
        if not self.can_apply(target, context):
            return {'success': False, 'reason': 'Invalid target for healing'}
        
        old_hp = target.hp
        target.hp = min(target.max_hp, target.hp + self.magnitude)
        healing_done = target.hp - old_hp
        
        return {
            'success': True,
            'healing_done': healing_done,
            'target_hp': target.hp,
            'target_max_hp': target.max_hp
        }


class StatModifierEffect(Effect):
    """Effect that temporarily modifies unit stats."""
    
    def __init__(self, stat_name: str, modifier: Union[int, float], duration: int, 
                 source_id: str = None, is_percentage: bool = False):
        super().__init__(EffectType.STAT_MODIFIER, modifier, duration, source_id)
        self.stat_name = stat_name
        self.is_percentage = is_percentage
        
        modifier_text = f"{modifier}%" if is_percentage else f"{modifier:+d}"
        self.description = f"{modifier_text} {stat_name} for {duration} turns"
    
    def can_apply(self, target: Any, context: Dict[str, Any]) -> bool:
        """Check if stat modifier can be applied."""
        # Must be a unit with the specified stat
        return hasattr(target, self.stat_name)
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply stat modifier to target."""
        if not self.can_apply(target, context):
            return {'success': False, 'reason': f'Target does not have stat: {self.stat_name}'}
        
        # TODO: Implement temporary stat modifier system
        # For now, just return success
        return {
            'success': True,
            'stat_modified': self.stat_name,
            'modifier': self.magnitude,
            'duration': self.duration,
            'note': 'Stat modifier system not yet implemented'
        }


class ResourceEffect(Effect):
    """Effect that modifies unit resources (MP, AP, etc.)."""
    
    def __init__(self, resource_type: ResourceType, amount: int, duration: int = 0, source_id: str = None):
        super().__init__(EffectType.RESOURCE_CHANGE, amount, duration, source_id)
        self.resource_type = resource_type
        
        action = "restores" if amount > 0 else "drains"
        self.description = f"{action.title()} {abs(amount)} {resource_type.value.upper()}"
    
    def can_apply(self, target: Any, context: Dict[str, Any]) -> bool:
        """Check if resource effect can be applied."""
        resource_attr = self.resource_type.value
        max_resource_attr = f"max_{resource_attr}"
        
        return hasattr(target, resource_attr) and hasattr(target, max_resource_attr)
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply resource change to target."""
        if not self.can_apply(target, context):
            return {'success': False, 'reason': f'Target does not have resource: {self.resource_type.value}'}
        
        resource_attr = self.resource_type.value
        max_resource_attr = f"max_{resource_attr}"
        
        old_value = getattr(target, resource_attr)
        max_value = getattr(target, max_resource_attr)
        
        # Apply change with bounds checking
        new_value = max(0, min(max_value, old_value + self.magnitude))
        setattr(target, resource_attr, new_value)
        
        actual_change = new_value - old_value
        
        return {
            'success': True,
            'resource_type': self.resource_type.value,
            'change': actual_change,
            'new_value': new_value,
            'max_value': max_value
        }


class EffectFactory:
    """Factory for creating effects from configuration data."""
    
    @staticmethod
    def create_from_talent_data(effect_name: str, effect_data: Any, source_id: str = None) -> Optional[Effect]:
        """
        Create effect from talent data.
        
        Args:
            effect_name: Name of the effect (e.g., 'base_damage', 'healing_amount')
            effect_data: Effect value or configuration
            source_id: Source talent/action ID
            
        Returns:
            Effect object or None if unrecognized
        """
        effect_data = int(effect_data) if isinstance(effect_data, str) and effect_data.isdigit() else effect_data
        
        # Damage effects
        if 'damage' in effect_name.lower():
            damage_type = DamageType.PHYSICAL
            if 'magical' in effect_name.lower():
                damage_type = DamageType.MAGICAL
            elif 'spiritual' in effect_name.lower():
                damage_type = DamageType.SPIRITUAL
            return DamageEffect(effect_data, source_id=source_id, damage_type=damage_type)
        
        # Healing effects
        elif 'heal' in effect_name.lower():
            return HealingEffect(effect_data, source_id=source_id)
        
        # Resource effects
        elif 'mp_restoration' in effect_name.lower():
            return ResourceEffect(ResourceType.MP, effect_data, source_id=source_id)
        elif 'hp_restoration' in effect_name.lower():
            return HealingEffect(effect_data, source_id=source_id)
        
        # Stat modifiers
        elif 'stat_bonus' in effect_name.lower():
            # Need additional data for stat name and duration
            return None  # Will be handled by specific talent parsing
        
        return None
    
    @staticmethod
    def create_multiple_from_talent(talent_data) -> List[Effect]:
        """Create all effects from talent data."""
        effects = []
        
        if not hasattr(talent_data, 'effects'):
            return effects
        
        source_id = getattr(talent_data, 'id', 'unknown')
        
        for effect_name, effect_value in talent_data.effects.items():
            effect = EffectFactory.create_from_talent_data(effect_name, effect_value, source_id)
            if effect:
                effects.append(effect)
        
        return effects