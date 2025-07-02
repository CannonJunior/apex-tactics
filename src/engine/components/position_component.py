"""
Position Component

Manages unit position, facing direction, and movement state
for battlefield positioning and tactical gameplay.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

from ...core.ecs import Component
from ...core.math import GridPosition


@dataclass
class PositionComponent(Component):
    """Component for unit position and orientation"""
    
    position: GridPosition = GridPosition(0, 0)
    previous_position: Optional[GridPosition] = None
    facing_direction: int = 0  # 0=North, 1=East, 2=South, 3=West
    height: float = 0.0  # Height for elevation bonuses
    
    # Movement state
    has_moved: bool = False
    movement_remaining: int = 3
    max_movement: int = 3
    can_move: bool = True
    
    # Position flags
    is_flying: bool = False
    is_hidden: bool = False  # For stealth mechanics
    
    def move_to(self, new_position: GridPosition) -> bool:
        """Move to new position if possible"""
        if not self.can_move or self.movement_remaining <= 0:
            return False
        
        # Calculate movement cost (simplified - would need battlefield integration)
        movement_cost = self.position.manhattan_distance(new_position)
        
        if movement_cost > self.movement_remaining:
            return False
        
        self.previous_position = self.position
        self.position = new_position
        self.movement_remaining -= movement_cost
        self.has_moved = True
        
        return True
    
    def set_facing(self, target_position: GridPosition):
        """Set facing direction towards target"""
        dx = target_position.x - self.position.x
        dy = target_position.y - self.position.y
        
        if abs(dx) > abs(dy):
            self.facing_direction = 1 if dx > 0 else 3  # East or West
        else:
            self.facing_direction = 2 if dy > 0 else 0  # South or North
    
    def get_facing_vector(self) -> tuple:
        """Get facing direction as vector"""
        directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # N, E, S, W
        return directions[self.facing_direction]
    
    def is_facing(self, target_position: GridPosition) -> bool:
        """Check if facing towards target position"""
        dx, dy = self.get_facing_vector()
        target_dx = target_position.x - self.position.x
        target_dy = target_position.y - self.position.y
        
        # Check if target is in facing direction
        if dx != 0:
            return (dx > 0 and target_dx > 0) or (dx < 0 and target_dx < 0)
        else:
            return (dy > 0 and target_dy > 0) or (dy < 0 and target_dy < 0)
    
    def get_flanking_positions(self) -> list:
        """Get positions that would be flanking this unit"""
        facing_dx, facing_dy = self.get_facing_vector()
        
        # Flanking positions are behind and to the sides
        flanking_positions = []
        
        # Behind
        behind_x = self.position.x - facing_dx
        behind_y = self.position.y - facing_dy
        flanking_positions.append(GridPosition(behind_x, behind_y))
        
        # Sides (perpendicular to facing)
        if facing_dx == 0:  # Facing N/S, sides are E/W
            flanking_positions.append(GridPosition(self.position.x + 1, self.position.y))
            flanking_positions.append(GridPosition(self.position.x - 1, self.position.y))
        else:  # Facing E/W, sides are N/S
            flanking_positions.append(GridPosition(self.position.x, self.position.y + 1))
            flanking_positions.append(GridPosition(self.position.x, self.position.y - 1))
        
        return flanking_positions
    
    def reset_movement(self):
        """Reset movement for new turn"""
        self.movement_remaining = self.max_movement
        self.has_moved = False
        self.can_move = True
    
    def prevent_movement(self):
        """Prevent movement (e.g., due to status effects)"""
        self.can_move = False
        self.movement_remaining = 0
    
    def get_distance_to(self, other_position: GridPosition) -> int:
        """Get Manhattan distance to another position"""
        return self.position.manhattan_distance(other_position)
    
    def is_adjacent_to(self, other_position: GridPosition) -> bool:
        """Check if adjacent to another position"""
        return self.get_distance_to(other_position) == 1
    
    def is_in_range(self, target_position: GridPosition, range_value: int) -> bool:
        """Check if target is within range"""
        return self.get_distance_to(target_position) <= range_value
    
    def teleport_to(self, new_position: GridPosition):
        """Teleport to position without movement cost"""
        self.previous_position = self.position
        self.position = new_position
    
    def get_height_advantage(self, other_position: 'PositionComponent') -> float:
        """Get height advantage over another position"""
        return self.height - other_position.height
    
    def has_height_advantage(self, other_position: 'PositionComponent') -> bool:
        """Check if has height advantage"""
        return self.height > other_position.height
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize component to dictionary"""
        return {
            "position": {"x": self.position.x, "y": self.position.y},
            "previous_position": (
                {"x": self.previous_position.x, "y": self.previous_position.y} 
                if self.previous_position else None
            ),
            "facing_direction": self.facing_direction,
            "height": self.height,
            "has_moved": self.has_moved,
            "movement_remaining": self.movement_remaining,
            "max_movement": self.max_movement,
            "can_move": self.can_move,
            "is_flying": self.is_flying,
            "is_hidden": self.is_hidden
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Deserialize component from dictionary"""
        pos_data = data.get("position", {"x": 0, "y": 0})
        self.position = GridPosition(pos_data["x"], pos_data["y"])
        
        prev_pos_data = data.get("previous_position")
        if prev_pos_data:
            self.previous_position = GridPosition(prev_pos_data["x"], prev_pos_data["y"])
        
        self.facing_direction = data.get("facing_direction", 0)
        self.height = data.get("height", 0.0)
        self.has_moved = data.get("has_moved", False)
        self.movement_remaining = data.get("movement_remaining", 3)
        self.max_movement = data.get("max_movement", 3)
        self.can_move = data.get("can_move", True)
        self.is_flying = data.get("is_flying", False)
        self.is_hidden = data.get("is_hidden", False)