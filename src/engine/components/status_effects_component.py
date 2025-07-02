"""
Status Effects Component

Manages temporary status effects, buffs, debuffs, and conditions
affecting unit capabilities and combat performance.
"""

from typing import Dict, Any, List, Set
from dataclasses import dataclass, field
from enum import Enum

from ...core.ecs import Component


class StatusEffectType(str, Enum):
    """Types of status effects"""
    BUFF = "buff"
    DEBUFF = "debuff"
    CONDITION = "condition"
    DAMAGE_OVER_TIME = "damage_over_time"
    HEAL_OVER_TIME = "heal_over_time"


class StatusEffect(str, Enum):
    """Predefined status effects"""
    # Damage over time
    POISON = "poison"
    BURN = "burn"
    BLEED = "bleed"
    
    # Healing over time
    REGENERATION = "regeneration"
    BLESSED = "blessed"
    
    # Movement effects
    STUNNED = "stunned"
    SLOWED = "slowed"
    HASTED = "hasted"
    ROOTED = "rooted"
    
    # Combat effects
    BLIND = "blind"
    CONFUSED = "confused"
    FEARED = "feared"
    CHARMED = "charmed"
    
    # Stat buffs
    ATTACK_BOOST = "attack_boost"
    DEFENSE_BOOST = "defense_boost"
    ACCURACY_BOOST = "accuracy_boost"
    CRITICAL_BOOST = "critical_boost"
    
    # Stat debuffs
    ATTACK_PENALTY = "attack_penalty"
    DEFENSE_PENALTY = "defense_penalty"
    ACCURACY_PENALTY = "accuracy_penalty"
    
    # Special conditions
    INVISIBLE = "invisible"
    PROTECTED = "protected"
    VULNERABLE = "vulnerable"
    FOCUSED = "focused"
    BERSERK = "berserk"


@dataclass
class StatusEffectData:
    """Data for a single status effect instance"""
    effect_type: StatusEffect
    duration: float
    intensity: float = 1.0
    source_id: str = ""
    description: str = ""
    stack_count: int = 1
    max_stacks: int = 1
    
    def tick(self, delta_time: float) -> bool:
        """Tick the effect duration, return True if expired"""
        self.duration -= delta_time
        return self.duration <= 0
    
    def can_stack_with(self, other: 'StatusEffectData') -> bool:
        """Check if can stack with another effect of same type"""
        return (self.effect_type == other.effect_type and 
                self.stack_count < self.max_stacks)


@dataclass
class StatusEffectsComponent(Component):
    """Component for managing status effects"""
    
    # Active effects with remaining duration
    active_effects: Dict[str, float] = field(default_factory=dict)
    
    # Detailed effect data
    effect_data: Dict[str, StatusEffectData] = field(default_factory=dict)
    
    # Effect immunities
    immunities: Set[str] = field(default_factory=set)
    
    # Effect resistances (0.0 to 1.0, reduces duration)
    resistances: Dict[str, float] = field(default_factory=dict)
    
    # Effect history for AI learning
    effect_history: List[str] = field(default_factory=list)
    
    def add_effect(self, effect_name: str, duration: float, intensity: float = 1.0, 
                  source_id: str = "", max_stacks: int = 1) -> bool:
        """Add a status effect"""
        # Check immunity
        if effect_name in self.immunities:
            return False
        
        # Apply resistance
        resistance = self.resistances.get(effect_name, 0.0)
        effective_duration = duration * (1.0 - resistance)
        
        if effective_duration <= 0:
            return False
        
        # Handle stacking
        if effect_name in self.effect_data:
            existing_effect = self.effect_data[effect_name]
            
            if existing_effect.can_stack_with(StatusEffectData(
                effect_type=StatusEffect(effect_name),
                duration=effective_duration,
                intensity=intensity,
                source_id=source_id,
                max_stacks=max_stacks
            )):
                # Stack the effect
                existing_effect.stack_count += 1
                existing_effect.intensity += intensity
                existing_effect.duration = max(existing_effect.duration, effective_duration)
            else:
                # Replace if new duration is longer
                if effective_duration > existing_effect.duration:
                    existing_effect.duration = effective_duration
                    existing_effect.intensity = intensity
        else:
            # Add new effect
            self.effect_data[effect_name] = StatusEffectData(
                effect_type=StatusEffect(effect_name),
                duration=effective_duration,
                intensity=intensity,
                source_id=source_id,
                max_stacks=max_stacks
            )
        
        self.active_effects[effect_name] = self.effect_data[effect_name].duration
        self.effect_history.append(effect_name)
        
        return True
    
    def remove_effect(self, effect_name: str) -> bool:
        """Remove a status effect"""
        if effect_name in self.active_effects:
            del self.active_effects[effect_name]
        
        if effect_name in self.effect_data:
            del self.effect_data[effect_name]
            return True
        
        return False
    
    def has_effect(self, effect_name: str) -> bool:
        """Check if has specific effect"""
        return effect_name in self.active_effects
    
    def get_effect_intensity(self, effect_name: str) -> float:
        """Get intensity of specific effect"""
        if effect_name in self.effect_data:
            return self.effect_data[effect_name].intensity
        return 0.0
    
    def get_effect_duration(self, effect_name: str) -> float:
        """Get remaining duration of effect"""
        return self.active_effects.get(effect_name, 0.0)
    
    def get_effect_stacks(self, effect_name: str) -> int:
        """Get number of stacks for effect"""
        if effect_name in self.effect_data:
            return self.effect_data[effect_name].stack_count
        return 0
    
    def update_effects(self, delta_time: float) -> List[str]:
        """Update all effects, return list of expired effects"""
        expired_effects = []
        
        for effect_name in list(self.active_effects.keys()):
            if effect_name in self.effect_data:
                if self.effect_data[effect_name].tick(delta_time):
                    expired_effects.append(effect_name)
                    self.remove_effect(effect_name)
                else:
                    self.active_effects[effect_name] = self.effect_data[effect_name].duration
        
        return expired_effects
    
    def add_immunity(self, effect_name: str):
        """Add immunity to specific effect"""
        self.immunities.add(effect_name)
        
        # Remove effect if currently active
        if effect_name in self.active_effects:
            self.remove_effect(effect_name)
    
    def remove_immunity(self, effect_name: str):
        """Remove immunity to specific effect"""
        self.immunities.discard(effect_name)
    
    def add_resistance(self, effect_name: str, resistance: float):
        """Add resistance to specific effect (0.0 to 1.0)"""
        self.resistances[effect_name] = max(0.0, min(1.0, resistance))
    
    def remove_resistance(self, effect_name: str):
        """Remove resistance to specific effect"""
        if effect_name in self.resistances:
            del self.resistances[effect_name]
    
    def is_immune_to(self, effect_name: str) -> bool:
        """Check if immune to specific effect"""
        return effect_name in self.immunities
    
    def get_resistance_to(self, effect_name: str) -> float:
        """Get resistance value for specific effect"""
        return self.resistances.get(effect_name, 0.0)
    
    def clear_all_effects(self):
        """Clear all active effects"""
        self.active_effects.clear()
        self.effect_data.clear()
    
    def clear_effects_by_type(self, effect_type: StatusEffectType):
        """Clear all effects of specific type"""
        to_remove = []
        
        for effect_name, effect_data in self.effect_data.items():
            if self._get_effect_type(effect_name) == effect_type:
                to_remove.append(effect_name)
        
        for effect_name in to_remove:
            self.remove_effect(effect_name)
    
    def _get_effect_type(self, effect_name: str) -> StatusEffectType:
        """Get type of status effect"""
        damage_over_time = [StatusEffect.POISON, StatusEffect.BURN, StatusEffect.BLEED]
        heal_over_time = [StatusEffect.REGENERATION, StatusEffect.BLESSED]
        debuffs = [
            StatusEffect.STUNNED, StatusEffect.SLOWED, StatusEffect.BLIND,
            StatusEffect.CONFUSED, StatusEffect.FEARED, StatusEffect.ATTACK_PENALTY,
            StatusEffect.DEFENSE_PENALTY, StatusEffect.ACCURACY_PENALTY, StatusEffect.VULNERABLE
        ]
        buffs = [
            StatusEffect.HASTED, StatusEffect.ATTACK_BOOST, StatusEffect.DEFENSE_BOOST,
            StatusEffect.ACCURACY_BOOST, StatusEffect.CRITICAL_BOOST, StatusEffect.PROTECTED,
            StatusEffect.FOCUSED, StatusEffect.BERSERK
        ]
        
        try:
            effect_enum = StatusEffect(effect_name)
            if effect_enum in damage_over_time:
                return StatusEffectType.DAMAGE_OVER_TIME
            elif effect_enum in heal_over_time:
                return StatusEffectType.HEAL_OVER_TIME
            elif effect_enum in debuffs:
                return StatusEffectType.DEBUFF
            elif effect_enum in buffs:
                return StatusEffectType.BUFF
            else:
                return StatusEffectType.CONDITION
        except ValueError:
            return StatusEffectType.CONDITION
    
    def get_effects_by_type(self, effect_type: StatusEffectType) -> List[str]:
        """Get all active effects of specific type"""
        effects = []
        for effect_name in self.active_effects.keys():
            if self._get_effect_type(effect_name) == effect_type:
                effects.append(effect_name)
        return effects
    
    def has_any_debuff(self) -> bool:
        """Check if has any debuff effect"""
        return len(self.get_effects_by_type(StatusEffectType.DEBUFF)) > 0
    
    def has_any_buff(self) -> bool:
        """Check if has any buff effect"""
        return len(self.get_effects_by_type(StatusEffectType.BUFF)) > 0
    
    def can_act(self) -> bool:
        """Check if unit can perform actions (not stunned, etc.)"""
        disabling_effects = [StatusEffect.STUNNED, StatusEffect.FEARED, StatusEffect.CHARMED]
        return not any(self.has_effect(effect.value) for effect in disabling_effects)
    
    def can_move(self) -> bool:
        """Check if unit can move"""
        movement_blocking = [StatusEffect.STUNNED, StatusEffect.ROOTED, StatusEffect.FEARED]
        return not any(self.has_effect(effect.value) for effect in movement_blocking)
    
    def get_movement_modifier(self) -> float:
        """Get movement speed modifier from effects"""
        modifier = 1.0
        
        if self.has_effect(StatusEffect.SLOWED.value):
            modifier *= 0.5
        
        if self.has_effect(StatusEffect.HASTED.value):
            modifier *= 1.5
        
        return modifier
    
    def get_attack_modifier(self) -> float:
        """Get attack damage modifier from effects"""
        modifier = 1.0
        
        if self.has_effect(StatusEffect.ATTACK_BOOST.value):
            modifier += 0.5 * self.get_effect_intensity(StatusEffect.ATTACK_BOOST.value)
        
        if self.has_effect(StatusEffect.ATTACK_PENALTY.value):
            modifier -= 0.3 * self.get_effect_intensity(StatusEffect.ATTACK_PENALTY.value)
        
        if self.has_effect(StatusEffect.BERSERK.value):
            modifier += 0.8  # Significant attack boost but loses defense
        
        return max(0.1, modifier)  # Minimum 10% damage
    
    def get_defense_modifier(self) -> float:
        """Get defense modifier from effects"""
        modifier = 1.0
        
        if self.has_effect(StatusEffect.DEFENSE_BOOST.value):
            modifier += 0.4 * self.get_effect_intensity(StatusEffect.DEFENSE_BOOST.value)
        
        if self.has_effect(StatusEffect.DEFENSE_PENALTY.value):
            modifier -= 0.3 * self.get_effect_intensity(StatusEffect.DEFENSE_PENALTY.value)
        
        if self.has_effect(StatusEffect.VULNERABLE.value):
            modifier -= 0.5
        
        if self.has_effect(StatusEffect.PROTECTED.value):
            modifier += 0.6
        
        if self.has_effect(StatusEffect.BERSERK.value):
            modifier -= 0.4  # Reduced defense when berserk
        
        return max(0.1, modifier)  # Minimum 10% defense
    
    def get_accuracy_modifier(self) -> float:
        """Get accuracy modifier from effects"""
        modifier = 1.0
        
        if self.has_effect(StatusEffect.ACCURACY_BOOST.value):
            modifier += 0.3 * self.get_effect_intensity(StatusEffect.ACCURACY_BOOST.value)
        
        if self.has_effect(StatusEffect.ACCURACY_PENALTY.value):
            modifier -= 0.2 * self.get_effect_intensity(StatusEffect.ACCURACY_PENALTY.value)
        
        if self.has_effect(StatusEffect.BLIND.value):
            modifier -= 0.5
        
        if self.has_effect(StatusEffect.FOCUSED.value):
            modifier += 0.4
        
        return max(0.1, modifier)  # Minimum 10% accuracy
    
    def get_critical_modifier(self) -> float:
        """Get critical hit chance modifier from effects"""
        modifier = 1.0
        
        if self.has_effect(StatusEffect.CRITICAL_BOOST.value):
            modifier += 0.5 * self.get_effect_intensity(StatusEffect.CRITICAL_BOOST.value)
        
        if self.has_effect(StatusEffect.FOCUSED.value):
            modifier += 0.3
        
        return modifier
    
    def is_hidden(self) -> bool:
        """Check if unit is hidden/invisible"""
        return self.has_effect(StatusEffect.INVISIBLE.value)
    
    def get_effect_summary(self) -> Dict[str, Any]:
        """Get summary of all active effects"""
        return {
            "active_count": len(self.active_effects),
            "buffs": self.get_effects_by_type(StatusEffectType.BUFF),
            "debuffs": self.get_effects_by_type(StatusEffectType.DEBUFF),
            "damage_over_time": self.get_effects_by_type(StatusEffectType.DAMAGE_OVER_TIME),
            "heal_over_time": self.get_effects_by_type(StatusEffectType.HEAL_OVER_TIME),
            "can_act": self.can_act(),
            "can_move": self.can_move(),
            "is_hidden": self.is_hidden()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize component to dictionary"""
        effect_data_dict = {}
        for name, data in self.effect_data.items():
            effect_data_dict[name] = {
                "effect_type": data.effect_type.value,
                "duration": data.duration,
                "intensity": data.intensity,
                "source_id": data.source_id,
                "description": data.description,
                "stack_count": data.stack_count,
                "max_stacks": data.max_stacks
            }
        
        return {
            "active_effects": self.active_effects.copy(),
            "effect_data": effect_data_dict,
            "immunities": list(self.immunities),
            "resistances": self.resistances.copy(),
            "effect_history": self.effect_history.copy()
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Deserialize component from dictionary"""
        self.active_effects = data.get("active_effects", {})
        
        effect_data_dict = data.get("effect_data", {})
        self.effect_data = {}
        for name, effect_dict in effect_data_dict.items():
            self.effect_data[name] = StatusEffectData(
                effect_type=StatusEffect(effect_dict["effect_type"]),
                duration=effect_dict["duration"],
                intensity=effect_dict.get("intensity", 1.0),
                source_id=effect_dict.get("source_id", ""),
                description=effect_dict.get("description", ""),
                stack_count=effect_dict.get("stack_count", 1),
                max_stacks=effect_dict.get("max_stacks", 1)
            )
        
        self.immunities = set(data.get("immunities", []))
        self.resistances = data.get("resistances", {})
        self.effect_history = data.get("effect_history", [])