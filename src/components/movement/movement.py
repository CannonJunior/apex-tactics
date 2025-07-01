"""
Movement Component

Component for handling unit movement capabilities and ranges.
"""

from dataclasses import dataclass
from core.ecs.component import BaseComponent


@dataclass
class MovementComponent(BaseComponent):
    """
    Component that defines a unit's movement capabilities.
    
    Attributes:
        movement_range: Number of tiles the unit can move per turn
        movement_speed: Animation speed for movement (for visual purposes)
        can_move_diagonal: Whether unit can move diagonally
        movement_cost_multiplier: Multiplier for movement costs on difficult terrain
    """
    
    def __init__(self, movement_range: int = 3, movement_speed: float = 1.0, 
                 can_move_diagonal: bool = True, movement_cost_multiplier: float = 1.0):
        """
        Initialize movement component.
        
        Args:
            movement_range: Number of tiles the unit can move per turn
            movement_speed: Animation speed for movement
            can_move_diagonal: Whether unit can move diagonally
            movement_cost_multiplier: Multiplier for terrain movement costs
        """
        super().__init__()
        self.movement_range = movement_range
        self.movement_speed = movement_speed
        self.can_move_diagonal = can_move_diagonal
        self.movement_cost_multiplier = movement_cost_multiplier
        
        # State tracking
        self.remaining_movement = movement_range
        self.has_moved_this_turn = False
    
    def can_move(self, distance: int = 1) -> bool:
        """Check if the unit can move the specified distance"""
        return self.remaining_movement >= distance and not self.has_moved_this_turn
    
    def consume_movement(self, distance: int):
        """Consume movement points for a move"""
        self.remaining_movement = max(0, self.remaining_movement - distance)
        if distance > 0:
            self.has_moved_this_turn = True
    
    def reset_movement(self):
        """Reset movement for a new turn"""
        self.remaining_movement = self.movement_range
        self.has_moved_this_turn = False
    
    def get_effective_movement_range(self) -> int:
        """Get the current effective movement range"""
        return self.remaining_movement if not self.has_moved_this_turn else 0
    
    def to_dict(self):
        """Serialize component to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'movement_range': self.movement_range,
            'movement_speed': self.movement_speed,
            'can_move_diagonal': self.can_move_diagonal,
            'movement_cost_multiplier': self.movement_cost_multiplier,
            'remaining_movement': self.remaining_movement,
            'has_moved_this_turn': self.has_moved_this_turn
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data):
        """Deserialize component from dictionary"""
        component = cls(
            movement_range=data.get('movement_range', 3),
            movement_speed=data.get('movement_speed', 1.0),
            can_move_diagonal=data.get('can_move_diagonal', True),
            movement_cost_multiplier=data.get('movement_cost_multiplier', 1.0)
        )
        
        # Restore state
        component.remaining_movement = data.get('remaining_movement', component.movement_range)
        component.has_moved_this_turn = data.get('has_moved_this_turn', False)
        
        return component