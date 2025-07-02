"""
Stats Component

Manages unit statistics including HP, MP, attributes, and combat stats
following the Apex Tactics stat system design.
"""

from typing import Dict, Any
from dataclasses import dataclass, field

from ...core.ecs import Component


@dataclass
class StatsComponent(Component):
    """Component for unit statistics"""
    
    # Basic stats
    max_hp: int = 100
    current_hp: int = 100
    max_mp: int = 10
    current_mp: int = 10
    level: int = 1
    experience: int = 0
    alive: bool = True
    
    # Core attributes (nine-attribute foundation)
    attributes: Dict[str, int] = field(default_factory=lambda: {
        # Primary attributes
        "strength": 10,      # Physical power and melee damage
        "fortitude": 10,     # Health and physical resistance
        "finesse": 10,       # Accuracy and agility
        "wisdom": 10,        # Magical power and MP
        "wonder": 10,        # Magical resistance and special abilities
        "worthy": 10,        # Leadership and morale
        "faith": 10,         # Spiritual power and healing
        "spirit": 10,        # Spiritual resistance and will
        "speed": 10,         # Movement and initiative
        
        # Derived combat stats (calculated from primary attributes)
        "physical_attack": 20,
        "magical_attack": 15,
        "spiritual_attack": 12,
        "physical_defense": 10,
        "magical_defense": 8,
        "spiritual_defense": 6,
        
        # Combat modifiers
        "accuracy": 85,
        "critical_chance": 5,
        "dodge_chance": 10,
        "block_chance": 5,
        
        # Movement and range
        "move_points": 3,
        "melee_range": 1,
        "ranged_range": 3,
        "spell_range": 4,
        "ability_range": 2,
        
        # Special attributes
        "initiative": 10,
        "leadership": 0,
        "morale": 50
    })
    
    # Temporary modifiers (buffs/debuffs)
    temporary_modifiers: Dict[str, float] = field(default_factory=dict)
    
    # Equipment modifiers
    equipment_bonuses: Dict[str, float] = field(default_factory=dict)
    
    def get_effective_attribute(self, attribute_name: str) -> float:
        """Get effective attribute value including all modifiers"""
        base_value = self.attributes.get(attribute_name, 0)
        temp_modifier = self.temporary_modifiers.get(attribute_name, 0)
        equipment_bonus = self.equipment_bonuses.get(attribute_name, 0)
        
        return base_value + temp_modifier + equipment_bonus
    
    def apply_temporary_modifier(self, attribute: str, value: float, duration: int = 3):
        """Apply temporary attribute modifier"""
        current_modifier = self.temporary_modifiers.get(attribute, 0)
        self.temporary_modifiers[attribute] = current_modifier + value
    
    def remove_temporary_modifier(self, attribute: str, value: float):
        """Remove temporary attribute modifier"""
        current_modifier = self.temporary_modifiers.get(attribute, 0)
        self.temporary_modifiers[attribute] = max(0, current_modifier - value)
        
        if self.temporary_modifiers[attribute] == 0:
            del self.temporary_modifiers[attribute]
    
    def calculate_derived_stats(self):
        """Calculate derived stats from primary attributes"""
        # HP calculation: base 50 + (fortitude * 5) + (strength * 2)
        self.max_hp = 50 + (self.attributes["fortitude"] * 5) + (self.attributes["strength"] * 2)
        
        # MP calculation: base 5 + (wisdom * 2) + (wonder * 1)
        self.max_mp = 5 + (self.attributes["wisdom"] * 2) + self.attributes["wonder"]
        
        # Physical attack: strength * 2 + finesse
        self.attributes["physical_attack"] = (self.attributes["strength"] * 2) + self.attributes["finesse"]
        
        # Magical attack: wisdom * 2 + wonder
        self.attributes["magical_attack"] = (self.attributes["wisdom"] * 2) + self.attributes["wonder"]
        
        # Spiritual attack: faith * 2 + spirit
        self.attributes["spiritual_attack"] = (self.attributes["faith"] * 2) + self.attributes["spirit"]
        
        # Physical defense: fortitude * 1.5 + strength * 0.5
        self.attributes["physical_defense"] = int((self.attributes["fortitude"] * 1.5) + (self.attributes["strength"] * 0.5))
        
        # Magical defense: wonder * 1.5 + wisdom * 0.5
        self.attributes["magical_defense"] = int((self.attributes["wonder"] * 1.5) + (self.attributes["wisdom"] * 0.5))
        
        # Spiritual defense: spirit * 1.5 + faith * 0.5
        self.attributes["spiritual_defense"] = int((self.attributes["spirit"] * 1.5) + (self.attributes["faith"] * 0.5))
        
        # Accuracy: base 70 + finesse * 1.5
        self.attributes["accuracy"] = 70 + int(self.attributes["finesse"] * 1.5)
        
        # Critical chance: base 2 + finesse * 0.3
        self.attributes["critical_chance"] = 2 + int(self.attributes["finesse"] * 0.3)
        
        # Dodge chance: finesse + speed * 0.5
        self.attributes["dodge_chance"] = self.attributes["finesse"] + int(self.attributes["speed"] * 0.5)
        
        # Initiative: speed * 2 + finesse
        self.attributes["initiative"] = (self.attributes["speed"] * 2) + self.attributes["finesse"]
        
        # Movement points: base 2 + speed * 0.2
        self.attributes["move_points"] = 2 + int(self.attributes["speed"] * 0.2)
        
        # Ensure current values don't exceed maximums
        if self.current_hp > self.max_hp:
            self.current_hp = self.max_hp
        if self.current_mp > self.max_mp:
            self.current_mp = self.max_mp
    
    def heal(self, amount: int) -> int:
        """Heal HP and return actual amount healed"""
        old_hp = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        return self.current_hp - old_hp
    
    def restore_mp(self, amount: int) -> int:
        """Restore MP and return actual amount restored"""
        old_mp = self.current_mp
        self.current_mp = min(self.max_mp, self.current_mp + amount)
        return self.current_mp - old_mp
    
    def take_damage(self, amount: int) -> bool:
        """Take damage and return True if unit dies"""
        self.current_hp = max(0, self.current_hp - amount)
        if self.current_hp <= 0:
            self.alive = False
            return True
        return False
    
    def consume_mp(self, amount: int) -> bool:
        """Consume MP and return True if successful"""
        if self.current_mp >= amount:
            self.current_mp -= amount
            return True
        return False
    
    def get_hp_percentage(self) -> float:
        """Get HP as percentage"""
        return self.current_hp / self.max_hp if self.max_hp > 0 else 0.0
    
    def get_mp_percentage(self) -> float:
        """Get MP as percentage"""
        return self.current_mp / self.max_mp if self.max_mp > 0 else 0.0
    
    def is_at_full_health(self) -> bool:
        """Check if at full health"""
        return self.current_hp == self.max_hp
    
    def is_low_health(self, threshold: float = 0.25) -> bool:
        """Check if health is below threshold"""
        return self.get_hp_percentage() < threshold
    
    def is_critical_health(self, threshold: float = 0.1) -> bool:
        """Check if health is critically low"""
        return self.get_hp_percentage() < threshold
    
    def can_act(self) -> bool:
        """Check if unit can perform actions"""
        return self.alive and self.current_hp > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize component to dictionary"""
        return {
            "max_hp": self.max_hp,
            "current_hp": self.current_hp,
            "max_mp": self.max_mp,
            "current_mp": self.current_mp,
            "level": self.level,
            "experience": self.experience,
            "alive": self.alive,
            "attributes": self.attributes.copy(),
            "temporary_modifiers": self.temporary_modifiers.copy(),
            "equipment_bonuses": self.equipment_bonuses.copy()
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Deserialize component from dictionary"""
        self.max_hp = data.get("max_hp", 100)
        self.current_hp = data.get("current_hp", 100)
        self.max_mp = data.get("max_mp", 10)
        self.current_mp = data.get("current_mp", 10)
        self.level = data.get("level", 1)
        self.experience = data.get("experience", 0)
        self.alive = data.get("alive", True)
        self.attributes = data.get("attributes", {})
        self.temporary_modifiers = data.get("temporary_modifiers", {})
        self.equipment_bonuses = data.get("equipment_bonuses", {})