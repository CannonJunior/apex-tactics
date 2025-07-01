"""
Defense System Components

Implements multi-layered defense system with physical, magical, and spiritual defense types.
"""

from core.ecs.component import BaseComponent
from .damage import AttackType


class DefenseComponent(BaseComponent):
    """
    Component providing multi-layered defense capabilities.
    
    Implements three distinct defense types:
    - Physical Defense: Against physical attacks
    - Magical Defense: Against magical attacks  
    - Spiritual Defense: Against spiritual attacks
    """
    
    def __init__(self,
                 physical_defense: int = 0,
                 magical_defense: int = 0,
                 spiritual_defense: int = 0,
                 armor_rating: int = 0,
                 magic_resistance: int = 0,
                 spiritual_ward: int = 0):
        """
        Initialize defense component.
        
        Args:
            physical_defense: Base physical defense value
            magical_defense: Base magical defense value
            spiritual_defense: Base spiritual defense value
            armor_rating: Additional physical armor rating
            magic_resistance: Additional magical resistance
            spiritual_ward: Additional spiritual protection
        """
        super().__init__()
        
        # Base defense values (derived from stats)
        self.physical_defense = physical_defense
        self.magical_defense = magical_defense  
        self.spiritual_defense = spiritual_defense
        
        # Equipment/modifier bonuses
        self.armor_rating = armor_rating
        self.magic_resistance = magic_resistance
        self.spiritual_ward = spiritual_ward
    
    def get_defense_value(self, attack_type: AttackType) -> int:
        """
        Get total defense value for the specified attack type.
        
        Args:
            attack_type: Type of incoming attack
            
        Returns:
            Total defense value including base defense and bonuses
        """
        defense_map = {
            AttackType.PHYSICAL: self.physical_defense + self.armor_rating,
            AttackType.MAGICAL: self.magical_defense + self.magic_resistance,
            AttackType.SPIRITUAL: self.spiritual_defense + self.spiritual_ward
        }
        return max(0, defense_map[attack_type])
    
    def add_armor_bonus(self, physical: int = 0, magical: int = 0, spiritual: int = 0):
        """Add armor bonuses from equipment or modifiers"""
        self.armor_rating += physical
        self.magic_resistance += magical
        self.spiritual_ward += spiritual
    
    def remove_armor_bonus(self, physical: int = 0, magical: int = 0, spiritual: int = 0):
        """Remove armor bonuses (e.g., when equipment is removed)"""
        self.armor_rating = max(0, self.armor_rating - physical)
        self.magic_resistance = max(0, self.magic_resistance - magical)
        self.spiritual_ward = max(0, self.spiritual_ward - spiritual)
    
    def get_defense_breakdown(self) -> dict:
        """Get detailed breakdown of defense values for debugging"""
        return {
            'physical': {
                'base': self.physical_defense,
                'armor': self.armor_rating,
                'total': self.get_defense_value(AttackType.PHYSICAL)
            },
            'magical': {
                'base': self.magical_defense,
                'resistance': self.magic_resistance,
                'total': self.get_defense_value(AttackType.MAGICAL)
            },
            'spiritual': {
                'base': self.spiritual_defense,
                'ward': self.spiritual_ward,
                'total': self.get_defense_value(AttackType.SPIRITUAL)
            }
        }
    
    def to_dict(self):
        """Serialize component to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'physical_defense': self.physical_defense,
            'magical_defense': self.magical_defense,
            'spiritual_defense': self.spiritual_defense,
            'armor_rating': self.armor_rating,
            'magic_resistance': self.magic_resistance,
            'spiritual_ward': self.spiritual_ward
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data):
        """Deserialize component from dictionary"""
        return cls(
            physical_defense=data.get('physical_defense', 0),
            magical_defense=data.get('magical_defense', 0),
            spiritual_defense=data.get('spiritual_defense', 0),
            armor_rating=data.get('armor_rating', 0),
            magic_resistance=data.get('magic_resistance', 0),
            spiritual_ward=data.get('spiritual_ward', 0)
        )