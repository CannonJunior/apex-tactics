"""
Tactical Movement Component

Handles movement-specific data for tactical RPG units.
Extends the base MovementComponent with tactical-specific features.
"""

from typing import Dict, Any
from dataclasses import dataclass

from core.ecs.component import BaseComponent

@dataclass
class TacticalMovementComponent(BaseComponent):
    """
    Component for tactical movement data.
    
    Works alongside the base MovementComponent to provide
    tactical RPG specific movement mechanics.
    """
    
    def __init__(self, 
                 movement_points: int = 3,
                 movement_range: int = 3,
                 action_points: int = 3):
        super().__init__()
        
        # Movement system from apex-tactics.py
        self.max_movement_points = movement_points
        self.current_movement_points = movement_points
        self.movement_range = movement_range  # Max tiles per turn
        
        # Action system
        self.max_action_points = action_points
        self.current_action_points = action_points
        
        # Movement state
        self.has_moved_this_turn = False
        self.movement_path = []  # Path for current planned movement
        
        # Movement costs (can be modified by terrain, effects, etc.)
        self.base_movement_cost = 1  # Cost per tile
        self.diagonal_movement_cost = 1  # Cost for diagonal movement
    
    def can_move(self, distance: int = 1) -> bool:
        """
        Check if unit can move the specified distance.
        
        Args:
            distance: Number of tiles to move
            
        Returns:
            True if movement is possible
        """
        required_points = distance * self.base_movement_cost
        return (self.current_movement_points >= required_points and 
                distance <= self.movement_range)
    
    def consume_movement(self, distance: int) -> bool:
        """
        Consume movement points for movement.
        
        Args:
            distance: Distance moved
            
        Returns:
            True if movement was successful
        """
        if not self.can_move(distance):
            return False
        
        cost = distance * self.base_movement_cost
        self.current_movement_points -= cost
        self.has_moved_this_turn = True
        return True
    
    def can_act(self, action_cost: int = 1) -> bool:
        """
        Check if unit can perform action.
        
        Args:
            action_cost: AP cost of action
            
        Returns:
            True if action is possible
        """
        return self.current_action_points >= action_cost
    
    def consume_action_points(self, cost: int) -> bool:
        """
        Consume action points for actions.
        
        Args:
            cost: Action point cost
            
        Returns:
            True if action was successful
        """
        if not self.can_act(cost):
            return False
        
        self.current_action_points -= cost
        return True
    
    def refresh_for_new_turn(self):
        """Refresh movement and action points for new turn"""
        self.current_movement_points = self.max_movement_points
        self.current_action_points = self.max_action_points
        self.has_moved_this_turn = False
        self.movement_path.clear()
    
    def get_remaining_movement(self) -> int:
        """Get remaining movement distance this turn"""
        return min(
            self.current_movement_points // self.base_movement_cost,
            self.movement_range
        )
    
    def is_exhausted(self) -> bool:
        """Check if unit has no remaining actions this turn"""
        return (self.current_movement_points <= 0 and 
                self.current_action_points <= 0)
    
    def plan_movement(self, path: list):
        """
        Plan movement path for validation.
        
        Args:
            path: List of positions for movement path
        """
        self.movement_path = path.copy()
    
    def clear_movement_plan(self):
        """Clear planned movement"""
        self.movement_path.clear()
    
    def get_movement_summary(self) -> Dict[str, Any]:
        """Get movement state summary"""
        return {
            'movement_points': f"{self.current_movement_points}/{self.max_movement_points}",
            'action_points': f"{self.current_action_points}/{self.max_action_points}",
            'movement_range': self.movement_range,
            'has_moved': self.has_moved_this_turn,
            'remaining_movement': self.get_remaining_movement(),
            'is_exhausted': self.is_exhausted(),
            'planned_moves': len(self.movement_path)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize component to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'max_movement_points': self.max_movement_points,
            'current_movement_points': self.current_movement_points,
            'movement_range': self.movement_range,
            'max_action_points': self.max_action_points,
            'current_action_points': self.current_action_points,
            'has_moved_this_turn': self.has_moved_this_turn,
            'movement_path': self.movement_path,
            'base_movement_cost': self.base_movement_cost,
            'diagonal_movement_cost': self.diagonal_movement_cost,
            'movement_summary': self.get_movement_summary()
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TacticalMovementComponent':
        """Deserialize component from dictionary"""
        component = cls(
            movement_points=data.get('max_movement_points', 3),
            movement_range=data.get('movement_range', 3),
            action_points=data.get('max_action_points', 3)
        )
        
        # Restore base component data
        component.entity_id = data.get('entity_id')
        component.created_at = data.get('created_at', component.created_at)
        component.component_id = data.get('component_id', component.component_id)
        
        # Restore current state
        component.current_movement_points = data.get('current_movement_points', component.max_movement_points)
        component.current_action_points = data.get('current_action_points', component.max_action_points)
        component.has_moved_this_turn = data.get('has_moved_this_turn', False)
        component.movement_path = data.get('movement_path', [])
        component.base_movement_cost = data.get('base_movement_cost', 1)
        component.diagonal_movement_cost = data.get('diagonal_movement_cost', 1)
        
        return component
    
    def __str__(self) -> str:
        return f"Movement: {self.current_movement_points}/{self.max_movement_points}, Actions: {self.current_action_points}/{self.max_action_points}"
    
    def __repr__(self) -> str:
        return f"TacticalMovementComponent(mp={self.current_movement_points}/{self.max_movement_points}, ap={self.current_action_points}/{self.max_action_points})"