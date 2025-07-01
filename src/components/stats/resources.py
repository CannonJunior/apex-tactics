"""
Three-Resource System

Implements MP (regenerating), Rage (building/decaying), and Kwan (location-based)
resources from Advanced-Implementation-Guide.md
"""

from typing import Dict, Any, List
import time
from dataclasses import dataclass
from enum import Enum

from core.ecs.component import BaseComponent

class ResourceType(Enum):
    """Resource type enumeration"""
    MP = "mp"
    RAGE = "rage"
    KWAN = "kwan"

class Resource:
    """
    Base resource class with common functionality.
    """
    
    def __init__(self, max_value: int, current_value: int = None):
        self.max_value = max_value
        self.current_value = current_value if current_value is not None else max_value
        self.last_update = time.time()
    
    @property
    def percentage(self) -> float:
        """Get resource as percentage of maximum"""
        return self.current_value / self.max_value if self.max_value > 0 else 0.0
    
    @property
    def is_full(self) -> bool:
        """Check if resource is at maximum"""
        return self.current_value >= self.max_value
    
    @property
    def is_empty(self) -> bool:
        """Check if resource is depleted"""
        return self.current_value <= 0
    
    def add(self, amount: int) -> int:
        """
        Add to resource value.
        
        Args:
            amount: Amount to add
            
        Returns:
            Actual amount added (clamped to max)
        """
        old_value = self.current_value
        self.current_value = min(self.max_value, self.current_value + amount)
        return self.current_value - old_value
    
    def subtract(self, amount: int) -> int:
        """
        Subtract from resource value.
        
        Args:
            amount: Amount to subtract
            
        Returns:
            Actual amount subtracted (clamped to 0)
        """
        old_value = self.current_value
        self.current_value = max(0, self.current_value - amount)
        return old_value - self.current_value
    
    def set_value(self, value: int):
        """Set resource to specific value"""
        self.current_value = max(0, min(self.max_value, value))
    
    def set_max_value(self, max_value: int):
        """Update maximum value and adjust current if needed"""
        self.max_value = max_value
        self.current_value = min(self.current_value, self.max_value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize resource to dictionary"""
        return {
            'max_value': self.max_value,
            'current_value': self.current_value,
            'percentage': self.percentage,
            'last_update': self.last_update
        }

class MPResource(Resource):
    """
    Mana Points - regenerating resource for spells and abilities.
    
    Regenerates over time at a steady rate.
    """
    
    def __init__(self, max_value: int, regen_rate: float = 5.0, 
                 current_value: int = None):
        super().__init__(max_value, current_value)
        self.regen_rate = regen_rate  # Points per second
        self.regen_delay = 0.0        # Delay before regeneration starts
        self.combat_regen_modifier = 0.5  # Reduced regen in combat
        self.in_combat = False
    
    def update(self, delta_time: float):
        """
        Update MP regeneration.
        
        Args:
            delta_time: Time elapsed since last update
        """
        if self.is_full:
            return
        
        current_time = time.time()
        time_since_update = current_time - self.last_update
        
        # Apply regeneration delay
        if time_since_update < self.regen_delay:
            return
        
        # Calculate regeneration amount
        effective_regen_rate = self.regen_rate
        if self.in_combat:
            effective_regen_rate *= self.combat_regen_modifier
        
        regen_amount = int(effective_regen_rate * delta_time)
        self.add(regen_amount)
        
        self.last_update = current_time
    
    def set_combat_state(self, in_combat: bool):
        """Set combat state to affect regeneration"""
        self.in_combat = in_combat
    
    def set_regen_delay(self, delay: float):
        """Set delay before regeneration starts (e.g., after taking damage)"""
        self.regen_delay = delay
        self.last_update = time.time()

class RageResource(Resource):
    """
    Rage - builds from taking/dealing damage, decays over time.
    
    Increases when taking or dealing damage, slowly decays when inactive.
    """
    
    def __init__(self, max_value: int = 100, decay_rate: float = 0.05, 
                 current_value: int = 0):
        super().__init__(max_value, current_value)
        self.decay_rate = decay_rate  # Percentage per second (0.05 = 5%/sec)
        self.build_from_damage_taken = 1.5  # Multiplier for damage taken
        self.build_from_damage_dealt = 1.0   # Multiplier for damage dealt
        self.decay_threshold = 10  # Minimum rage before decay starts
    
    def update(self, delta_time: float):
        """
        Update rage decay.
        
        Args:
            delta_time: Time elapsed since last update
        """
        if self.current_value <= self.decay_threshold:
            return
        
        # Calculate decay amount
        decay_amount = int(self.current_value * self.decay_rate * delta_time)
        self.subtract(decay_amount)
        
        self.last_update = time.time()
    
    def add_from_damage_taken(self, damage: int) -> int:
        """
        Add rage from taking damage.
        
        Args:
            damage: Damage taken
            
        Returns:
            Rage gained
        """
        rage_gain = int(damage * self.build_from_damage_taken)
        return self.add(rage_gain)
    
    def add_from_damage_dealt(self, damage: int) -> int:
        """
        Add rage from dealing damage.
        
        Args:
            damage: Damage dealt
            
        Returns:
            Rage gained
        """
        rage_gain = int(damage * self.build_from_damage_dealt)
        return self.add(rage_gain)
    
    def can_use_rage_ability(self, cost: int) -> bool:
        """Check if enough rage for ability"""
        return self.current_value >= cost

class KwanResource(Resource):
    """
    Kwan - location-based spiritual resource.
    
    Value depends on location type and spiritual resonance.
    Changes based on battlefield position and environmental factors.
    """
    
    def __init__(self, base_value: int = 50, current_value: int = None):
        max_value = 100  # Kwan is always 0-100
        super().__init__(max_value, current_value if current_value is not None else base_value)
        self.base_value = base_value
        self.location_modifier = 0.0
        self.environmental_modifiers: Dict[str, float] = {}
        self.spiritual_resonance = 1.0  # Multiplier based on faith/spirit stats
    
    def update_for_location(self, location_type: str, 
                           location_modifiers: Dict[str, float] = None):
        """
        Update Kwan based on current location.
        
        Args:
            location_type: Type of location (e.g., "temple", "battlefield", "forest")
            location_modifiers: Optional additional modifiers
        """
        # Location type base modifiers
        location_base_modifiers = {
            'temple': 0.3,      # +30% in temples
            'shrine': 0.2,      # +20% at shrines
            'forest': 0.1,      # +10% in natural areas
            'battlefield': -0.1, # -10% on battlefields
            'corruption': -0.3,  # -30% in corrupted areas
            'void': -0.5,       # -50% in void zones
            'normal': 0.0       # No modifier for normal areas
        }
        
        self.location_modifier = location_base_modifiers.get(location_type, 0.0)
        
        # Apply additional modifiers
        if location_modifiers:
            self.environmental_modifiers.update(location_modifiers)
        
        self._recalculate_kwan()
    
    def set_spiritual_resonance(self, resonance: float):
        """
        Set spiritual resonance multiplier based on faith/spirit stats.
        
        Args:
            resonance: Multiplier (typically 0.5 to 2.0)
        """
        self.spiritual_resonance = max(0.1, resonance)
        self._recalculate_kwan()
    
    def add_environmental_modifier(self, source: str, modifier: float):
        """Add environmental modifier from specific source"""
        self.environmental_modifiers[source] = modifier
        self._recalculate_kwan()
    
    def remove_environmental_modifier(self, source: str):
        """Remove environmental modifier"""
        if source in self.environmental_modifiers:
            del self.environmental_modifiers[source]
            self._recalculate_kwan()
    
    def _recalculate_kwan(self):
        """Recalculate Kwan value based on all modifiers"""
        # Start with base value
        total_modifier = self.location_modifier
        
        # Add environmental modifiers
        for modifier in self.environmental_modifiers.values():
            total_modifier += modifier
        
        # Apply spiritual resonance
        final_modifier = total_modifier * self.spiritual_resonance
        
        # Calculate final value
        final_value = int(self.base_value * (1.0 + final_modifier))
        self.set_value(final_value)

@dataclass
class ResourceManager(BaseComponent):
    """
    Component managing all three resources for an entity.
    
    Handles MP, Rage, and Kwan with their unique behaviors.
    """
    
    def __init__(self, max_mp: int = 100, max_rage: int = 100, base_kwan: int = 50):
        super().__init__()
        
        self.mp = MPResource(max_mp)
        self.rage = RageResource(max_rage)
        self.kwan = KwanResource(base_kwan)
        
        # Resource history for analytics
        self.resource_history: List[Dict[str, Any]] = []
        self.history_max_length = 100
    
    def update(self, delta_time: float, location_type: str = "normal",
               in_combat: bool = False):
        """
        Update all resources.
        
        Args:
            delta_time: Time elapsed since last update
            location_type: Current location type for Kwan
            in_combat: Whether entity is in combat
        """
        # Update MP
        self.mp.set_combat_state(in_combat)
        self.mp.update(delta_time)
        
        # Update Rage
        self.rage.update(delta_time)
        
        # Update Kwan based on location
        self.kwan.update_for_location(location_type)
        
        # Record resource state for history
        self._record_resource_state()
    
    def set_max_resources(self, max_mp: int = None, max_rage: int = None):
        """Update maximum resource values"""
        if max_mp is not None:
            self.mp.set_max_value(max_mp)
        if max_rage is not None:
            self.rage.set_max_value(max_rage)
    
    def get_resource_percentages(self) -> Dict[str, float]:
        """Get all resources as percentages"""
        return {
            'mp': self.mp.percentage,
            'rage': self.rage.percentage,
            'kwan': self.kwan.percentage
        }
    
    def can_afford_cost(self, mp_cost: int = 0, rage_cost: int = 0, 
                       kwan_cost: int = 0) -> bool:
        """Check if entity can afford resource costs"""
        return (self.mp.current_value >= mp_cost and
                self.rage.current_value >= rage_cost and
                self.kwan.current_value >= kwan_cost)
    
    def spend_resources(self, mp_cost: int = 0, rage_cost: int = 0, 
                       kwan_cost: int = 0) -> bool:
        """
        Spend resources if available.
        
        Returns:
            True if resources were spent successfully
        """
        if not self.can_afford_cost(mp_cost, rage_cost, kwan_cost):
            return False
        
        self.mp.subtract(mp_cost)
        self.rage.subtract(rage_cost)
        self.kwan.subtract(kwan_cost)
        return True
    
    def _record_resource_state(self):
        """Record current resource state in history"""
        state = {
            'timestamp': time.time(),
            'mp': self.mp.to_dict(),
            'rage': self.rage.to_dict(), 
            'kwan': self.kwan.to_dict()
        }
        
        self.resource_history.append(state)
        
        # Limit history size
        if len(self.resource_history) > self.history_max_length:
            self.resource_history = self.resource_history[-self.history_max_length:]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize component to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'mp': self.mp.to_dict(),
            'rage': self.rage.to_dict(),
            'kwan': self.kwan.to_dict(),
            'resource_percentages': self.get_resource_percentages()
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResourceManager':
        """Deserialize component from dictionary"""
        manager = cls(
            max_mp=data.get('mp', {}).get('max_value', 100),
            max_rage=data.get('rage', {}).get('max_value', 100),
            base_kwan=data.get('kwan', {}).get('current_value', 50)
        )
        
        # Restore resource states
        if 'mp' in data:
            mp_data = data['mp']
            manager.mp.current_value = mp_data.get('current_value', manager.mp.max_value)
        
        if 'rage' in data:
            rage_data = data['rage']
            manager.rage.current_value = rage_data.get('current_value', 0)
        
        if 'kwan' in data:
            kwan_data = data['kwan']
            manager.kwan.current_value = kwan_data.get('current_value', 50)
        
        # Restore base component data
        manager.entity_id = data.get('entity_id')
        manager.created_at = data.get('created_at', time.time())
        manager.component_id = data.get('component_id', manager.component_id)
        
        return manager