"""
Nine-Attribute Stat System

Implements the core nine-attribute system from Advanced-Implementation-Guide.md:
Physical: strength, fortitude, finesse
Mental: wisdom, wonder, worthy  
Spiritual: faith, spirit, speed
"""

from typing import Dict, Any
import time
from dataclasses import dataclass

from core.ecs.component import BaseComponent

@dataclass
class AttributeStats(BaseComponent):
    """
    Nine-attribute stat component with derived stat calculations.
    
    Implements the sophisticated stat system with performance optimization
    to meet <1ms calculation target for complex character sheets.
    """
    
    def __init__(self, 
                 strength: int = 10, fortitude: int = 10, finesse: int = 10,
                 wisdom: int = 10, wonder: int = 10, worthy: int = 10,
                 faith: int = 10, spirit: int = 10, speed: int = 10):
        super().__init__()
        
        # Physical attributes
        self.strength = strength      # Physical power, melee damage
        self.fortitude = fortitude    # Health, physical defense
        self.finesse = finesse        # Dexterity, accuracy, dodge
        
        # Mental attributes
        self.wisdom = wisdom          # Magic defense, MP pool
        self.wonder = wonder          # Magic power, spell damage
        self.worthy = worthy          # Tactical awareness, initiative
        
        # Spiritual attributes
        self.faith = faith            # Spiritual power, healing
        self.spirit = spirit          # Spiritual defense, resistance
        self.speed = speed            # Movement, action speed
        
        # Cache for derived stats (performance optimization)
        self._derived_cache: Dict[str, int] = {}
        self._cache_timestamp = 0.0
        self._cache_valid = False
        
        # Current health and mana (initialized after derived stats are calculated)
        self._current_hp = None
        self._current_mp = None
    
    @property
    def derived_stats(self) -> Dict[str, int]:
        """
        Calculate all derived stats with caching for performance.
        
        Target: <1ms for complex character sheets
        
        Returns:
            Dictionary of derived stat values
        """
        current_time = time.time()
        
        # Use cache if valid and recent (within 100ms)
        if (self._cache_valid and 
            current_time - self._cache_timestamp < 0.1):
            return self._derived_cache.copy()
        
        # Recalculate derived stats
        self._derived_cache = {
            # Health and mana pools
            'hp': self.fortitude * 10 + self.strength * 2,
            'mp': self.wisdom * 8 + self.wonder * 3,
            
            # Physical combat stats
            'physical_attack': int(self.strength * 1.5 + self.finesse * 0.5),
            'physical_defense': int(self.fortitude * 1.2 + self.strength * 0.3),
            'physical_accuracy': int(self.finesse * 1.3 + self.worthy * 0.4),
            'physical_dodge': int(self.finesse * 1.1 + self.speed * 0.6),
            
            # Magical combat stats
            'magical_attack': int(self.wonder * 1.4 + self.wisdom * 0.6),
            'magical_defense': int(self.wisdom * 1.3 + self.wonder * 0.4),
            'magical_accuracy': int(self.wonder * 1.2 + self.worthy * 0.5),
            'magical_resistance': int(self.wisdom * 1.1 + self.spirit * 0.7),
            
            # Spiritual combat stats
            'spiritual_attack': int(self.faith * 1.3 + self.spirit * 0.5),
            'spiritual_defense': int(self.spirit * 1.2 + self.faith * 0.4),
            'spiritual_accuracy': int(self.faith * 1.1 + self.worthy * 0.6),
            'spiritual_resistance': int(self.spirit * 1.3 + self.wisdom * 0.3),
            
            # Movement and action stats
            'movement_speed': int(self.speed * 1.5 + self.finesse * 0.3),
            'initiative': int(self.speed * 0.8 + self.worthy * 1.0 + self.finesse * 0.4),
            'action_points': int((self.speed + self.worthy) / 5) + 3,
            
            # Special derived stats
            'carry_capacity': int(self.strength * 5 + self.fortitude * 2),
            'spell_slots': int(self.wisdom / 3) + int(self.wonder / 4) + 1,
            'critical_chance': int(self.finesse * 0.8 + self.worthy * 0.5),
            'mental_resistance': int(self.wisdom * 0.7 + self.worthy * 0.9 + self.spirit * 0.6)
        }
        
        self._cache_timestamp = current_time
        self._cache_valid = True
        
        return self._derived_cache.copy()
    
    @property
    def max_hp(self) -> int:
        """Get maximum health points"""
        return self.derived_stats['hp']
    
    @property
    def current_hp(self) -> int:
        """Get current health points"""
        if self._current_hp is None:
            self._current_hp = self.max_hp
        return self._current_hp
    
    @current_hp.setter
    def current_hp(self, value: int):
        """Set current health points"""
        self._current_hp = max(0, min(value, self.max_hp))
    
    @property
    def max_mp(self) -> int:
        """Get maximum mana points"""
        return self.derived_stats['mp']
    
    @property
    def current_mp(self) -> int:
        """Get current mana points"""
        if self._current_mp is None:
            self._current_mp = self.max_mp
        return self._current_mp
    
    @current_mp.setter
    def current_mp(self, value: int):
        """Set current mana points"""
        self._current_mp = max(0, min(value, self.max_mp))
    
    def get_attribute_total(self) -> int:
        """Get sum of all base attributes"""
        return (self.strength + self.fortitude + self.finesse +
                self.wisdom + self.wonder + self.worthy +
                self.faith + self.spirit + self.speed)
    
    def get_physical_total(self) -> int:
        """Get sum of physical attributes"""
        return self.strength + self.fortitude + self.finesse
    
    def get_mental_total(self) -> int:
        """Get sum of mental attributes"""
        return self.wisdom + self.wonder + self.worthy
    
    def get_spiritual_total(self) -> int:
        """Get sum of spiritual attributes"""
        return self.faith + self.spirit + self.speed
    
    def modify_attribute(self, attribute: str, value: int):
        """
        Modify base attribute and invalidate cache.
        
        Args:
            attribute: Name of attribute to modify
            value: New value for attribute
        """
        if hasattr(self, attribute):
            setattr(self, attribute, max(1, value))  # Minimum value of 1
            self._invalidate_cache()
        else:
            raise ValueError(f"Unknown attribute: {attribute}")
    
    def add_to_attribute(self, attribute: str, bonus: int):
        """
        Add bonus to attribute.
        
        Args:
            attribute: Name of attribute to modify
            bonus: Amount to add (can be negative)
        """
        if hasattr(self, attribute):
            current_value = getattr(self, attribute)
            self.modify_attribute(attribute, current_value + bonus)
        else:
            raise ValueError(f"Unknown attribute: {attribute}")
    
    def _invalidate_cache(self):
        """Mark derived stat cache as invalid"""
        self._cache_valid = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize component to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            # Base attributes
            'strength': self.strength,
            'fortitude': self.fortitude,
            'finesse': self.finesse,
            'wisdom': self.wisdom,
            'wonder': self.wonder,
            'worthy': self.worthy,
            'faith': self.faith,
            'spirit': self.spirit,
            'speed': self.speed,
            
            # Include derived stats for completeness
            'derived_stats': self.derived_stats,
            
            # Current health and mana
            'current_hp': self.current_hp,
            'current_mp': self.current_mp
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AttributeStats':
        """Deserialize component from dictionary"""
        attributes = cls(
            strength=data.get('strength', 10),
            fortitude=data.get('fortitude', 10),
            finesse=data.get('finesse', 10),
            wisdom=data.get('wisdom', 10),
            wonder=data.get('wonder', 10),
            worthy=data.get('worthy', 10),
            faith=data.get('faith', 10),
            spirit=data.get('spirit', 10),
            speed=data.get('speed', 10)
        )
        
        # Restore base component data
        attributes.entity_id = data.get('entity_id')
        attributes.created_at = data.get('created_at', time.time())
        attributes.component_id = data.get('component_id', attributes.component_id)
        
        # Restore current health and mana if provided
        if 'current_hp' in data:
            attributes._current_hp = data['current_hp']
        if 'current_mp' in data:
            attributes._current_mp = data['current_mp']
        
        return attributes
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for monitoring"""
        return {
            'cache_valid': self._cache_valid,
            'cache_age_ms': (time.time() - self._cache_timestamp) * 1000,
            'derived_stat_count': len(self._derived_cache)
        }