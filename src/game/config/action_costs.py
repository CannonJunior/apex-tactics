"""
Action Costs Configuration

Defines action point costs for all available actions in the tactical RPG.
"""

from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class ActionCosts:
    """Configuration class for action point costs."""
    
    # Movement costs
    MOVE_PER_TILE: int = 1   # AP cost per tile moved
    
    # Basic action costs
    BASIC_ATTACK: int = 30   # Standard physical attack
    BASIC_MAGIC: int = 25    # Standard magic spell
    SPIRIT_ACTION: int = 20  # Spirit-based actions
    
    # Inventory costs
    USE_ITEM: int = 15       # Using consumable items
    EQUIP_ITEM: int = 20     # Equipping/unequipping gear
    
    # Special action costs
    WAIT: int = 0            # Waiting/passing turn
    GUARD: int = 15          # Defensive stance
    
    # Movement mode costs
    MOVEMENT_MODE_ENTER: int = 5   # Cost to enter movement mode
    
    @classmethod
    def get_movement_cost(cls, distance: int) -> int:
        """Calculate movement cost based on distance."""
        return cls.MOVE_PER_TILE * distance
    
    @classmethod
    def get_talent_cost(cls, talent_data) -> int:
        """Get AP cost for a talent, with fallback to action type defaults."""
        if talent_data and talent_data.cost:
            # Use talent-specific AP cost if defined
            return talent_data.cost.get('ap_cost', 0)
        
        # Fallback to action type defaults if no specific cost
        if talent_data and hasattr(talent_data, 'action_type'):
            action_type = talent_data.action_type.lower()
            if action_type == 'attack':
                return cls.BASIC_ATTACK
            elif action_type == 'magic':
                return cls.BASIC_MAGIC
            elif action_type == 'spirit':
                return cls.SPIRIT_ACTION
        
        return 0
    
    @classmethod
    def get_action_cost(cls, action_type: str) -> int:
        """Get AP cost for basic action types."""
        action_costs = {
            'attack': cls.BASIC_ATTACK,
            'magic': cls.BASIC_MAGIC,
            'spirit': cls.SPIRIT_ACTION,
            'inventory': cls.USE_ITEM,
            'guard': cls.GUARD,
            'wait': cls.WAIT,
            'move': cls.MOVEMENT_MODE_ENTER
        }
        
        return action_costs.get(action_type.lower(), 0)

# Global instance for easy access
ACTION_COSTS = ActionCosts()