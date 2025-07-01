"""
Temporary Modifier System

Implements advanced buff/debuff mechanics with sophisticated stacking rules
from Advanced-Implementation-Guide.md
"""

from typing import Dict, Any, List, Optional, Set
import time
from dataclasses import dataclass
from enum import Enum
import uuid

from core.ecs.component import BaseComponent

class ModifierType(Enum):
    """Type of stat modifier"""
    FLAT = "flat"                    # Adds/subtracts fixed amount
    PERCENTAGE = "percentage"        # Multiplies by percentage
    MULTIPLICATIVE = "multiplicative" # Multiplies final value
    SET_VALUE = "set_value"         # Sets stat to specific value

class ModifierSource(Enum):
    """Source of the modifier"""
    EQUIPMENT = "equipment"
    SPELL = "spell"
    ABILITY = "ability"
    AURA = "aura"
    CONSUMABLE = "consumable"
    ENVIRONMENTAL = "environmental"
    STATUS_EFFECT = "status_effect"

class StackingRule(Enum):
    """How modifiers stack with others"""
    NONE = "none"           # Only one instance allowed
    UNLIMITED = "unlimited" # Stack without limit
    LIMITED = "limited"     # Stack up to maximum count
    REPLACE = "replace"     # Replace existing modifier from same source
    HIGHEST = "highest"     # Only highest value applies
    LOWEST = "lowest"       # Only lowest value applies

@dataclass
class Modifier:
    """
    Individual stat modifier with stacking and timing rules.
    """
    
    def __init__(self, 
                 stat_name: str,
                 modifier_type: ModifierType,
                 value: float,
                 duration: float = 0.0,  # 0 = permanent
                 source: ModifierSource = ModifierSource.SPELL,
                 source_id: str = "",
                 stacking_rule: StackingRule = StackingRule.UNLIMITED,
                 stack_limit: int = 0,  # 0 = no limit
                 priority: int = 0,    # Higher priority applies first
                 modifier_id: str = None):
        
        self.modifier_id = modifier_id or str(uuid.uuid4())
        self.stat_name = stat_name
        self.modifier_type = modifier_type
        self.value = value
        self.source = source
        self.source_id = source_id
        self.duration = duration
        self.stacking_rule = stacking_rule
        self.stack_limit = stack_limit
        self.priority = priority
        
        self.created_at = time.time()
        self.expires_at = self.created_at + duration if duration > 0 else 0.0
        self.active = True
    
    @property
    def is_expired(self) -> bool:
        """Check if modifier has expired"""
        if self.duration <= 0:
            return False  # Permanent modifier
        return time.time() >= self.expires_at
    
    @property
    def remaining_duration(self) -> float:
        """Get remaining duration in seconds"""
        if self.duration <= 0:
            return float('inf')  # Permanent
        return max(0.0, self.expires_at - time.time())
    
    def can_stack_with(self, other: 'Modifier') -> bool:
        """
        Check if this modifier can stack with another.
        
        Args:
            other: Other modifier to check stacking with
            
        Returns:
            True if modifiers can stack
        """
        # Must affect same stat
        if self.stat_name != other.stat_name:
            return True  # Different stats always stack
        
        # Check stacking rules
        if self.stacking_rule == StackingRule.NONE:
            return False  # No stacking allowed
        
        if self.stacking_rule == StackingRule.REPLACE:
            return self.source_id != other.source_id  # Replace same source
        
        if self.stacking_rule == StackingRule.UNLIMITED:
            return True  # Always stack
        
        # For LIMITED, HIGHEST, LOWEST - stacking logic handled in ModifierManager
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize modifier to dictionary"""
        return {
            'modifier_id': self.modifier_id,
            'stat_name': self.stat_name,
            'modifier_type': self.modifier_type.value,
            'value': self.value,
            'source': self.source.value,
            'source_id': self.source_id,
            'duration': self.duration,
            'stacking_rule': self.stacking_rule.value,
            'stack_limit': self.stack_limit,
            'priority': self.priority,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'active': self.active,
            'remaining_duration': self.remaining_duration
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Modifier':
        """Deserialize modifier from dictionary"""
        modifier = cls(
            modifier_id=data.get('modifier_id'),
            stat_name=data.get('stat_name', ''),
            modifier_type=ModifierType(data.get('modifier_type', 'flat')),
            value=data.get('value', 0.0),
            source=ModifierSource(data.get('source', 'spell')),
            source_id=data.get('source_id', ''),
            duration=data.get('duration', 0.0),
            stacking_rule=StackingRule(data.get('stacking_rule', 'unlimited')),
            stack_limit=data.get('stack_limit', 0),
            priority=data.get('priority', 0)
        )
        
        modifier.created_at = data.get('created_at', time.time())
        modifier.expires_at = data.get('expires_at', 0.0)
        modifier.active = data.get('active', True)
        
        return modifier

class ModifierManager(BaseComponent):
    """
    Component managing temporary modifiers for an entity.
    
    Handles complex stacking rules and stat calculation with performance optimization.
    Target: <1ms for complex character sheets with many modifiers.
    """
    
    def __init__(self):
        super().__init__()
        
        self.modifiers: List[Modifier] = []
        self.modifier_cache: Dict[str, float] = {}  # stat_name -> final_modifier
        self.cache_timestamp = 0.0
        self.cache_valid = False
        
        # Performance tracking
        self.calculation_count = 0
        self.last_calculation_time = 0.0
    
    def add_modifier(self, modifier: Modifier) -> bool:
        """
        Add modifier with stacking rule validation.
        
        Args:
            modifier: Modifier to add
            
        Returns:
            True if modifier was added successfully
        """
        # Check for stacking conflicts
        existing_modifiers = [m for m in self.modifiers 
                            if m.stat_name == modifier.stat_name and m.active]
        
        # Handle stacking rules
        if modifier.stacking_rule == StackingRule.NONE:
            # Remove all existing modifiers for this stat
            for existing in existing_modifiers:
                existing.active = False
        
        elif modifier.stacking_rule == StackingRule.REPLACE:
            # Remove modifiers from same source
            for existing in existing_modifiers:
                if existing.source_id == modifier.source_id:
                    existing.active = False
        
        elif modifier.stacking_rule == StackingRule.LIMITED:
            # Limit number of active modifiers
            active_count = len([m for m in existing_modifiers if m.active])
            if active_count >= modifier.stack_limit:
                # Remove oldest modifier
                oldest = min(existing_modifiers, key=lambda m: m.created_at)
                oldest.active = False
        
        elif modifier.stacking_rule == StackingRule.HIGHEST:
            # Keep only highest value modifier
            for existing in existing_modifiers:
                if existing.value < modifier.value:
                    existing.active = False
                elif existing.value > modifier.value:
                    return False  # Don't add lower value modifier
        
        elif modifier.stacking_rule == StackingRule.LOWEST:
            # Keep only lowest value modifier
            for existing in existing_modifiers:
                if existing.value > modifier.value:
                    existing.active = False
                elif existing.value < modifier.value:
                    return False  # Don't add higher value modifier
        
        # Add the modifier
        self.modifiers.append(modifier)
        self._invalidate_cache()
        return True
    
    def remove_modifier(self, modifier_id: str) -> bool:
        """
        Remove modifier by ID.
        
        Args:
            modifier_id: ID of modifier to remove
            
        Returns:
            True if modifier was found and removed
        """
        for modifier in self.modifiers:
            if modifier.modifier_id == modifier_id:
                modifier.active = False
                self._invalidate_cache()
                return True
        return False
    
    def remove_modifiers_by_source(self, source_id: str) -> int:
        """
        Remove all modifiers from specific source.
        
        Args:
            source_id: Source ID to remove modifiers from
            
        Returns:
            Number of modifiers removed
        """
        removed_count = 0
        for modifier in self.modifiers:
            if modifier.source_id == source_id and modifier.active:
                modifier.active = False
                removed_count += 1
        
        if removed_count > 0:
            self._invalidate_cache()
        
        return removed_count
    
    def update(self, delta_time: float):
        """
        Update modifiers and remove expired ones.
        
        Args:
            delta_time: Time elapsed since last update
        """
        expired_count = 0
        
        for modifier in self.modifiers:
            if modifier.active and modifier.is_expired:
                modifier.active = False
                expired_count += 1
        
        if expired_count > 0:
            self._invalidate_cache()
        
        # Clean up old inactive modifiers periodically
        current_time = time.time()
        if current_time - self.last_calculation_time > 10.0:  # Every 10 seconds
            self._cleanup_inactive_modifiers()
    
    def calculate_final_stat(self, base_stat: int, stat_name: str) -> int:
        """
        Calculate final stat value with all modifiers applied.
        
        Args:
            base_stat: Base stat value
            stat_name: Name of stat being calculated
            
        Returns:
            Final stat value with modifiers
        """
        calculation_start = time.perf_counter()
        
        # Use cache if valid
        if self.cache_valid and stat_name in self.modifier_cache:
            cached_modifier = self.modifier_cache[stat_name]
            result = int(base_stat + cached_modifier)
            return max(0, result)  # Ensure non-negative
        
        # Get active modifiers for this stat
        active_modifiers = [m for m in self.modifiers 
                          if m.stat_name == stat_name and m.active and not m.is_expired]
        
        # Sort by priority (higher priority first)
        active_modifiers.sort(key=lambda m: m.priority, reverse=True)
        
        # Apply modifiers in order
        final_value = float(base_stat)
        
        # Apply flat modifiers first
        flat_total = sum(m.value for m in active_modifiers 
                        if m.modifier_type == ModifierType.FLAT)
        final_value += flat_total
        
        # Apply percentage modifiers
        percentage_total = sum(m.value for m in active_modifiers 
                             if m.modifier_type == ModifierType.PERCENTAGE)
        final_value *= (1.0 + percentage_total)
        
        # Apply multiplicative modifiers
        for modifier in active_modifiers:
            if modifier.modifier_type == ModifierType.MULTIPLICATIVE:
                final_value *= modifier.value
        
        # Handle set value modifiers (highest priority wins)
        set_value_modifiers = [m for m in active_modifiers 
                             if m.modifier_type == ModifierType.SET_VALUE]
        if set_value_modifiers:
            highest_priority = max(set_value_modifiers, key=lambda m: m.priority)
            final_value = highest_priority.value
        
        # Cache the result
        total_modifier = final_value - base_stat
        self.modifier_cache[stat_name] = total_modifier
        
        # Performance tracking
        self.calculation_count += 1
        self.last_calculation_time = time.perf_counter()
        calculation_time = self.last_calculation_time - calculation_start
        
        # Warn if calculation is slow
        if calculation_time > 0.001:  # 1ms target
            from core.utils.logging import Logger
            Logger.warning(f"Slow modifier calculation: {calculation_time*1000:.2f}ms for {stat_name}")
        
        return max(0, int(final_value))  # Ensure non-negative integer
    
    def get_modifiers_for_stat(self, stat_name: str) -> List[Modifier]:
        """Get all active modifiers affecting a specific stat"""
        return [m for m in self.modifiers 
                if m.stat_name == stat_name and m.active and not m.is_expired]
    
    def get_modifier_summary(self) -> Dict[str, Any]:
        """Get summary of all active modifiers"""
        active_modifiers = [m for m in self.modifiers if m.active and not m.is_expired]
        
        by_stat = {}
        for modifier in active_modifiers:
            if modifier.stat_name not in by_stat:
                by_stat[modifier.stat_name] = []
            by_stat[modifier.stat_name].append(modifier.to_dict())
        
        return {
            'total_active': len(active_modifiers),
            'by_stat': by_stat,
            'calculation_count': self.calculation_count,
            'cache_valid': self.cache_valid
        }
    
    def _invalidate_cache(self):
        """Invalidate modifier cache"""
        self.cache_valid = False
        self.modifier_cache.clear()
    
    def _cleanup_inactive_modifiers(self):
        """Remove old inactive modifiers to free memory"""
        current_time = time.time()
        cleanup_threshold = 60.0  # Remove modifiers inactive for 1 minute
        
        self.modifiers = [m for m in self.modifiers 
                         if m.active or (current_time - m.created_at) < cleanup_threshold]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize component to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'modifiers': [m.to_dict() for m in self.modifiers if m.active],
            'modifier_summary': self.get_modifier_summary()
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModifierManager':
        """Deserialize component from dictionary"""
        manager = cls()
        
        # Restore modifiers
        for modifier_data in data.get('modifiers', []):
            modifier = Modifier.from_dict(modifier_data)
            manager.modifiers.append(modifier)
        
        # Restore base component data
        manager.entity_id = data.get('entity_id')
        manager.created_at = data.get('created_at', time.time())
        manager.component_id = data.get('component_id', manager.component_id)
        
        return manager